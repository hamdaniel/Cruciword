import os
import struct
from typing import Mapping, Union


class BitArray:
    HEBREW_ALPHABET = "אבגדהוזחטיכלמנסעפצקרשת"

    FILE_MAGIC = b"BMAP"
    FILE_VERSION = 1

    # magic, version, word_length, logical_bit_count, bitmap_count
    HEADER_FORMAT = "<4sBHIQ"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(
        self,
        source: Union[int, bytes, bytearray, memoryview],
        logical_size: int | None = None,
        bitmap_index: int | None = None,
    ):
        """
        Two construction modes:

        1. Empty bitmap:
           BitArray(logical_size)

        2. Load one bitmap from an already-loaded file buffer:
           BitArray(file_bytes, logical_size, bitmap_index)

           - file_bytes: the full file already loaded into memory
           - logical_size: number of real bits in each bitmap in that file
           - bitmap_index: bitmap offset in bitmap units, not bytes
        """
        self.logical_size = 0
        self.data = bytearray()

        if isinstance(source, int):
            if logical_size is not None or bitmap_index is not None:
                raise TypeError(
                    "When source is an int, do not pass logical_size or bitmap_index"
                )
            self._init_empty(source)

        elif isinstance(source, (bytes, bytearray, memoryview)):
            if logical_size is None or bitmap_index is None:
                raise TypeError(
                    "When source is a loaded file buffer, "
                    "both logical_size and bitmap_index are required"
                )
            self._init_from_loaded_file(source, logical_size, bitmap_index)

        else:
            raise TypeError(
                "source must be either an int size or a loaded file buffer"
            )

    # -------------------------------------------------
    # BASIC PROPERTIES
    # -------------------------------------------------

    @property
    def stored_size(self) -> int:
        # Real bits + 1 metadata bit ("any")
        return self.logical_size + 1

    @property
    def any_bit_index(self) -> int:
        # The extra bit comes right after the real bits.
        return self.logical_size

    @property
    def bytes_per_bitmap(self) -> int:
        return (self.stored_size + 7) // 8

    def __len__(self) -> int:
        return self.logical_size

    def __repr__(self) -> str:
        return (
            f"BitArray(logical_size={self.logical_size}, "
            f"any={self.any()}, ones={self.count_ones()})"
        )

    # -------------------------------------------------
    # INITIALIZATION
    # -------------------------------------------------

    def _init_empty(self, logical_size: int) -> None:
        if not isinstance(logical_size, int):
            raise TypeError("logical_size must be an integer")
        if logical_size < 0:
            raise ValueError("logical_size must be non-negative")

        self.logical_size = logical_size
        self.data = bytearray(self.bytes_per_bitmap)
        self._clear_unused_tail_bits()
        self._set_any_bit(0)

    def _init_from_loaded_file(
        self,
        file_bytes: Union[bytes, bytearray, memoryview],
        logical_size: int,
        bitmap_index: int,
    ) -> None:
        if not isinstance(logical_size, int):
            raise TypeError("logical_size must be an integer")
        if logical_size < 0:
            raise ValueError("logical_size must be non-negative")
        if not isinstance(bitmap_index, int):
            raise TypeError("bitmap_index must be an integer")
        if bitmap_index < 0:
            raise ValueError("bitmap_index must be non-negative")

        file_view = memoryview(file_bytes)
        header = self.read_header(file_view)

        if header["logical_size"] != logical_size:
            raise ValueError(
                f"logical_size mismatch: constructor got {logical_size}, "
                f"file header says {header['logical_size']}"
            )

        bytes_per_bitmap = (logical_size + 1 + 7) // 8
        bitmap_count = header["bitmap_count"]

        if bitmap_index >= bitmap_count:
            raise IndexError(
                f"bitmap_index out of range: {bitmap_index} (bitmap_count={bitmap_count})"
            )

        start = self.HEADER_SIZE + bitmap_index * bytes_per_bitmap
        end = start + bytes_per_bitmap

        if end > len(file_view):
            raise ValueError("file is truncated")

        self.logical_size = logical_size
        self.data = bytearray(file_view[start:end])
        self._clear_unused_tail_bits()
        self._refresh_any_bit()

    # -------------------------------------------------
    # BIT HELPERS
    # -------------------------------------------------

    def _check_data_index(self, i: int) -> None:
        if not isinstance(i, int):
            raise TypeError("bit index must be an integer")
        if not (0 <= i < self.logical_size):
            raise IndexError(f"bit index out of range: {i}")

    def _check_compatible(self, other: "BitArray") -> None:
        if not isinstance(other, BitArray):
            raise TypeError("other must be a BitArray")
        if self.logical_size != other.logical_size:
            raise ValueError("BitArrays must have the same logical_size")

    def _get_raw_bit(self, i: int) -> int:
        byte_index = i // 8
        bit_index = i % 8
        return (self.data[byte_index] >> bit_index) & 1

    def _set_raw_bit(self, i: int, value: int) -> None:
        byte_index = i // 8
        bit_index = i % 8
        mask = 1 << bit_index

        if value:
            self.data[byte_index] |= mask
        else:
            self.data[byte_index] &= ~mask

    def _set_any_bit(self, value: int) -> None:
        self._set_raw_bit(self.any_bit_index, 1 if value else 0)

    def _get_any_bit(self) -> int:
        return self._get_raw_bit(self.any_bit_index)

    def _clear_unused_tail_bits(self) -> None:
        if not self.data:
            return

        remainder = self.stored_size % 8
        if remainder == 0:
            return

        mask = (1 << remainder) - 1
        self.data[-1] &= mask

    def _compute_any_from_data(self) -> int:
        if self.logical_size == 0:
            return 0

        full_bytes = self.logical_size // 8
        remainder = self.logical_size % 8

        for i in range(full_bytes):
            if self.data[i] != 0:
                return 1

        if remainder > 0:
            mask = (1 << remainder) - 1
            if self.data[full_bytes] & mask:
                return 1

        return 0

    def _refresh_any_bit(self) -> None:
        self._set_any_bit(self._compute_any_from_data())

    # -------------------------------------------------
    # DATA ACCESS
    # -------------------------------------------------

    def get(self, i: int) -> int:
        self._check_data_index(i)
        return self._get_raw_bit(i)

    def set(self, i: int, value: int) -> None:
        self._check_data_index(i)

        value = 1 if value else 0
        old_value = self._get_raw_bit(i)

        if old_value == value:
            return

        self._set_raw_bit(i, value)

        if value:
            self._set_any_bit(1)
        else:
            # We may have removed the last 1, so recompute.
            if self._get_any_bit():
                self._refresh_any_bit()

    def any(self) -> bool:
        return bool(self._get_any_bit())

    def clear_all(self) -> None:
        for i in range(len(self.data)):
            self.data[i] = 0
        self._set_any_bit(0)

    def set_all(self) -> None:
        if self.logical_size == 0:
            self.clear_all()
            return

        for i in range(len(self.data)):
            self.data[i] = 0xFF

        self._clear_unused_tail_bits()
        self._set_any_bit(1)

    def count_ones(self) -> int:
        if self.logical_size == 0:
            return 0

        full_bytes = self.logical_size // 8
        remainder = self.logical_size % 8

        total = 0

        for i in range(full_bytes):
            total += self.data[i].bit_count()

        if remainder > 0:
            mask = (1 << remainder) - 1
            total += (self.data[full_bytes] & mask).bit_count()

        return total

    def to_bytes(self) -> bytes:
        self._clear_unused_tail_bits()
        self._refresh_any_bit()
        return bytes(self.data)

    @classmethod
    def from_bytes(cls, logical_size: int, raw: bytes) -> "BitArray":
        expected_len = (logical_size + 1 + 7) // 8
        if len(raw) != expected_len:
            raise ValueError(
                f"raw length mismatch: got {len(raw)} bytes, expected {expected_len}"
            )

        obj = cls(logical_size)
        obj.data[:] = raw
        obj._clear_unused_tail_bits()
        obj._refresh_any_bit()
        return obj

    # -------------------------------------------------
    # PYTHON OPERATORS
    # -------------------------------------------------

    def __getitem__(self, i: int) -> int:
        return self.get(i)

    def __setitem__(self, i: int, value: int) -> None:
        self.set(i, value)

    def __or__(self, other: "BitArray") -> "BitArray":
        self._check_compatible(other)

        result = BitArray(self.logical_size)
        for i in range(len(self.data)):
            result.data[i] = self.data[i] | other.data[i]

        result._clear_unused_tail_bits()
        result._refresh_any_bit()
        return result

    def __and__(self, other: "BitArray") -> "BitArray":
        self._check_compatible(other)

        result = BitArray(self.logical_size)
        for i in range(len(self.data)):
            result.data[i] = self.data[i] & other.data[i]

        result._clear_unused_tail_bits()
        result._refresh_any_bit()
        return result

    def __ior__(self, other: "BitArray") -> "BitArray":
        self._check_compatible(other)

        for i in range(len(self.data)):
            self.data[i] |= other.data[i]

        self._clear_unused_tail_bits()
        self._refresh_any_bit()
        return self

    def __iand__(self, other: "BitArray") -> "BitArray":
        self._check_compatible(other)

        for i in range(len(self.data)):
            self.data[i] &= other.data[i]

        self._clear_unused_tail_bits()
        self._refresh_any_bit()
        return self

    # -------------------------------------------------
    # FILE FORMAT
    # -------------------------------------------------

    @classmethod
    def read_header(
        cls, file_bytes: Union[bytes, bytearray, memoryview]
    ) -> dict[str, int]:
        file_view = memoryview(file_bytes)

        if len(file_view) < cls.HEADER_SIZE:
            raise ValueError("file too short to contain a valid header")

        raw_header = file_view[: cls.HEADER_SIZE]
        magic, version, word_length, logical_size, bitmap_count = struct.unpack(
            cls.HEADER_FORMAT, raw_header
        )

        if magic != cls.FILE_MAGIC:
            raise ValueError("invalid file magic")
        if version != cls.FILE_VERSION:
            raise ValueError(f"unsupported file version: {version}")

        return {
            "version": version,
            "word_length": word_length,
            "logical_size": logical_size,
            "bitmap_count": bitmap_count,
        }

    @classmethod
    def load_file(cls, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    @classmethod
    def save_store(
        cls,
        path: str,
        word_length: int,
        logical_size: int,
        bitmaps_by_key: Mapping[tuple[int, str], "BitArray"],
        alphabet: str | None = None,
    ) -> None:
        """
        Writes one file for a single word length.

        Bitmaps are written in this order:
        - primary: position in word (1-based)
        - secondary: letter order in alphabet

        Each key in bitmaps_by_key is:
            (position, letter)

        Missing entries are written as all-zero bitmaps.
        """
        if alphabet is None:
            alphabet = cls.HEBREW_ALPHABET

        if not isinstance(word_length, int) or word_length <= 0:
            raise ValueError("word_length must be a positive integer")
        if not isinstance(logical_size, int) or logical_size < 0:
            raise ValueError("logical_size must be a non-negative integer")

        bitmap_count = word_length * len(alphabet)

        header = struct.pack(
            cls.HEADER_FORMAT,
            cls.FILE_MAGIC,
            cls.FILE_VERSION,
            word_length,
            logical_size,
            bitmap_count,
        )

        with open(path, "wb") as f:
            f.write(header)

            zero_bitmap = cls(logical_size)

            for position in range(1, word_length + 1):
                for letter in alphabet:
                    bitmap = bitmaps_by_key.get((position, letter), zero_bitmap)

                    if bitmap.logical_size != logical_size:
                        raise ValueError(
                            f"bitmap at {(position, letter)} has logical_size "
                            f"{bitmap.logical_size}, expected {logical_size}"
                        )

                    f.write(bitmap.to_bytes())

    @classmethod
    def bitmap_index_for(
        cls,
        position: int,
        letter: str,
        alphabet: str | None = None,
    ) -> int:
        """
        Position is 1-based.
        Letter index is 0-based within the alphabet.

        Example:
            position=2, letter='א'  -> 22
        when alphabet length is 22.
        """
        if alphabet is None:
            alphabet = cls.HEBREW_ALPHABET

        if not isinstance(position, int) or position <= 0:
            raise ValueError("position must be a positive integer")
        if len(letter) != 1:
            raise ValueError("letter must be a single character")

        try:
            letter_index = alphabet.index(letter)
        except ValueError:
            raise ValueError(f"letter {letter!r} is not in the alphabet") from None

        return (position - 1) * len(alphabet) + letter_index