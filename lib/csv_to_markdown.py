from typing import Optional

import csv


def handle_aligns(aligns):
    if not aligns:
        aligns_tuple = None
    else:
        aligns_tuple = tuple(aligns.lower().replace(" ", "").split(","))
    return aligns_tuple


class Csv2Markdown:
    def __init__(
        self,
        filepath: str,
        aligns: tuple = None,
        padding: int = 1,
        delimiter: str = ",",
        quotechar: str = '"',
        escapechar: Optional[str] = None,
    ):
        self.filepath = filepath
        self.aligns = aligns
        self.padding = padding
        self._csv_dict = _read_csv(
            filepath, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar
        )
        self._num_cols = len(self._csv_dict.keys())
        if aligns:
            if padding == 0:
                raise ValueError("Cannot use aligns with 0 padding.")
            self._validate_aligns(self.aligns)
        self._word_length_dict = _get_max_word_per_col(self._csv_dict)

    def get_table(self) -> str:
        """Method to return markdown formatted table as string
        """
        header, dashes = self._prep_header()
        table = header + dashes
        for row in self._prep_body():
            table += row
        return table

    def save_table(self, filepath: str, mode: str = "w"):
        table = self.get_table()
        with open(filepath, mode=mode) as save_file:
            save_file.write(table)

    def _validate_aligns(self, aligns):
        for align in aligns:
            if not align in ("l", "r", "c"):
                raise ValueError(
                    "Aligns must be a tuple of 'l', 'r' and 'c' for left, right and centre. Found {} instead".format(
                        align
                    )
                )
        if not len(aligns) == self._num_cols:
            raise ValueError(
                "You need to specify the alignment for all columns. There are {} columns, but you provided {} alignments".format(
                    self._num_cols, len(aligns)
                )
            )

    def _prep_header(self) -> str:
        word_length_dict = self._word_length_dict
        header = "|"
        dashes = "|"
        for col in range(self._num_cols):
            col_title = self._csv_dict[col][0]
            num_spaces = word_length_dict[col] - len(col_title) + self.padding
            num_dashes = word_length_dict[col]
            header += " " * self.padding + col_title + " " * num_spaces + "|"
            dashes += " " * (self.padding - 1)

            if not self.aligns or self.aligns[col] == "l":
                dashes += " " + "-" * num_dashes + " " * self.padding + "|"
            elif self.aligns[col] == "r":
                dashes += " " + "-" * num_dashes + ":" + " " * (self.padding - 1) + "|"
            elif self.aligns[col] == "c":
                dashes += (
                    ":-" + "-" * (num_dashes - 1) + ":" + " " * (self.padding - 1) + "|"
                )

        return header + "\n", dashes + "\n"

    def _prep_body(self) -> str:
        self._prep_header()
        num_rows = len(self._csv_dict[0])
        word_length_dict = self._word_length_dict
        for row_num in range(1, num_rows):
            row = "|"

            for col in range(self._num_cols):
                word = self._csv_dict[col][row_num]
                num_spaces = word_length_dict[col] - len(word) + self.padding - 1
                row += " " * self.padding + word + " " * num_spaces + " |"
            yield row + "\n"


def _get_max_word_per_col(csv_dict) -> dict:
    word_length_dict = {}
    for key in csv_dict:
        max_word_length = 0
        for val in csv_dict[key]:
            if len(val) > max_word_length:
                max_word_length = len(val)
        word_length_dict[key] = max_word_length
    return word_length_dict


def _read_csv(
    filepath: str, delimiter: str = ",", quotechar: str = '"', escapechar: str = ""
) -> dict:
    csv_dict = {}
    with open(filepath, "r") as csv_file:
        csv_reader = csv.reader(
            csv_file, delimiter=delimiter, quotechar=quotechar, escapechar=None
        )
        header = next(csv_reader)
        num_cols = len(header)
        for num in range(num_cols):
            csv_dict[num] = [header[num]]
        for row in csv_reader:
            for num in range(num_cols):
                csv_dict[num].append(row[num])
    return csv_dict