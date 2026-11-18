"""Importação de XLSX e CSV preservando o tipo real de cada célula.

Nada aqui interpreta valores: apenas lê, registra o tipo de origem, a
coordenada e os problemas estruturais (quantidade de colunas, linhas vazias).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
from dataclasses import dataclass, field
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


@dataclass
class Cell:
    value: Any
    kind: str  # vazio | texto | inteiro | decimal | data | booleano
    number_format: str = ""
    coord: str = ""

    @property
    def is_empty(self) -> bool:
        return self.kind == "vazio"


@dataclass
class RawRow:
    line: int  # linha física de origem (XLSX: nº da linha; CSV: linha inicial do registro)
    line_end: int
    cells: list[Cell]
    n_fields: int  # quantidade de campos interpretados nesta linha
    extra: list[Cell] = field(default_factory=list)  # campos além do cabeçalho


@dataclass
class ImportMetadata:
    nome_arquivo: str
    tamanho_bytes: int
    sha256: str
    formato: str
    planilha: str | None
    planilhas_disponiveis: list[str]
    linhas_fisicas: int
    registros_interpretados: int
    linhas_vazias_ignoradas: int
    cabecalhos: list[str]
    data_processamento: str
    codificacao: str | None = None
    separador: str | None = None
    avisos: list[str] = field(default_factory=list)


@dataclass
class RawTable:
    headers: list[str]
    rows: list[RawRow]
    meta: ImportMetadata


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _kind_of(value: Any) -> str:
    if value is None:
        return "vazio"
    if isinstance(value, bool):
        return "booleano"
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return "data"
    if isinstance(value, int):
        return "inteiro"
    if isinstance(value, float):
        return "decimal"
    if isinstance(value, str):
        return "vazio" if value == "" else "texto"
    return "texto"


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def detect_format(filename: str) -> str:
    low = filename.lower()
    if low.endswith((".xlsx", ".xlsm")):
        return "xlsx"
    if low.endswith(".csv"):
        return "csv"
    raise ValueError(f"Formato não suportado: {filename}. Use .xlsx ou .csv.")


# ---------------------------------------------------------------- XLSX
def list_sheets(data: bytes) -> list[str]:
    wb = load_workbook(io.BytesIO(data), read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def read_xlsx(data: bytes, filename: str, sheet: str | None = None) -> RawTable:
    wb = load_workbook(io.BytesIO(data), data_only=True)
    sheets = list(wb.sheetnames)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    max_row = ws.max_row or 0
    max_col = ws.max_column or 0
    header_cells = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
    # Cabeçalho: até a última célula não vazia da linha 1
    n_header = 0
    for i, v in enumerate(header_cells):
        if v is not None and str(v).strip() != "":
            n_header = i + 1
    headers = ["" if v is None else str(v) for v in header_cells[:n_header]]
    rows: list[RawRow] = []
    empty = 0
    for r in range(2, max_row + 1):
        cells: list[Cell] = []
        extra: list[Cell] = []
        for c in range(1, max_col + 1):
            cell = ws.cell(row=r, column=c)
            obj = Cell(cell.value, _kind_of(cell.value), cell.number_format or "", f"{get_column_letter(c)}{r}")
            (cells if c <= n_header else extra).append(obj)
        if all(x.is_empty for x in cells) and all(x.is_empty for x in extra):
            empty += 1
            continue
        extra_filled = [x for x in extra if not x.is_empty]
        n_fields = n_header + (max(i for i, x in enumerate(extra) if not x.is_empty) + 1 if extra_filled else 0)
        rows.append(RawRow(r, r, cells, n_fields, extra_filled))
    wb.close()
    meta = ImportMetadata(
        nome_arquivo=filename, tamanho_bytes=len(data), sha256=sha256_bytes(data), formato="xlsx",
        planilha=ws.title, planilhas_disponiveis=sheets, linhas_fisicas=max_row,
        registros_interpretados=len(rows), linhas_vazias_ignoradas=empty, cabecalhos=headers,
        data_processamento=_now(),
    )
    return RawTable(headers, rows, meta)


# ---------------------------------------------------------------- CSV
def _decode(data: bytes) -> tuple[str, str, list[str]]:
    avisos: list[str] = []
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8"), "utf-8 com BOM", avisos
    try:
        return data.decode("utf-8"), "utf-8", avisos
    except UnicodeDecodeError:
        avisos.append("Arquivo não está em UTF-8; lido como Windows-1252 (cp1252). Confira acentos.")
        return data.decode("cp1252", errors="replace"), "cp1252", avisos


def _detect_separator(text: str) -> str:
    """Conta ',' e ';' fora de aspas na primeira linha lógica (cabeçalho)."""
    counts = {",": 0, ";": 0}
    in_q = False
    for ch in text:
        if ch == '"':
            in_q = not in_q
        elif not in_q and ch in "\r\n":
            break
        elif not in_q and ch in counts:
            counts[ch] += 1
    return ";" if counts[";"] > counts[","] else ","


def _physical_lines(text: str) -> int:
    if text == "":
        return 0
    n = text.count("\n") + (text.count("\r") - text.count("\r\n"))
    if not text.endswith(("\n", "\r")):
        n += 1
    return n


def read_csv(data: bytes, filename: str) -> RawTable:
    text, enc, avisos = _decode(data)
    sep = _detect_separator(text)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=sep, quotechar='"', doublequote=True, strict=False)
    rows: list[RawRow] = []
    headers: list[str] = []
    prev_end = 0
    empty = 0
    for i, rec in enumerate(reader):
        start, end = prev_end + 1, reader.line_num
        prev_end = end
        if i == 0:
            headers = rec
            continue
        if len(rec) == 0 or all(f == "" for f in rec):
            empty += 1
            continue
        cells = []
        for j in range(len(headers)):
            v = rec[j] if j < len(rec) else None
            kind = "vazio" if v is None or v == "" else "texto"
            cells.append(Cell(v if v is not None else None, kind, "", f"linha {start}, coluna {j + 1}"))
        extra = [Cell(v, "vazio" if v == "" else "texto", "", f"linha {start}, coluna {len(headers) + k + 1}")
                 for k, v in enumerate(rec[len(headers):])]
        extra = [c for c in extra if not c.is_empty]
        rows.append(RawRow(start, end, cells, len(rec), extra))
    meta = ImportMetadata(
        nome_arquivo=filename, tamanho_bytes=len(data), sha256=sha256_bytes(data), formato="csv",
        planilha=None, planilhas_disponiveis=[], linhas_fisicas=_physical_lines(text),
        registros_interpretados=len(rows), linhas_vazias_ignoradas=empty, cabecalhos=headers,
        data_processamento=_now(), codificacao=enc, separador=sep, avisos=avisos,
    )
    return RawTable(headers, rows, meta)


def read_file(data: bytes, filename: str, sheet: str | None = None) -> RawTable:
    fmt = detect_format(filename)
    return read_xlsx(data, filename, sheet) if fmt == "xlsx" else read_csv(data, filename)
