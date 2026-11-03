"""Domínio e persistência do MVP. Python 3.10+; biblioteca padrão."""
from contextlib import contextmanager
from dataclasses import dataclass, fields
from decimal import Decimal
from pathlib import Path
import math
import sqlite3


def obrigatorio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{campo}: texto obrigatório")


@dataclass(frozen=True)
class Tecnico:
    nome: str
    matricula: str | None = None
    setor: str | None = None
    papel: str = "TECNICO"
    ativo: int = 1
    id: int | None = None

    def __post_init__(self):
        obrigatorio(self.nome, "nome")
        if self.papel not in {"TECNICO", "SOLICITANTE"} or self.ativo not in (0, 1):
            raise ValueError("Papel ou situação cadastral inválida")
        if self.matricula is not None:
            obrigatorio(self.matricula, "matrícula")


@dataclass(frozen=True)
class Equipamento:
    tag: str
    denominacao: str
    fabricante: str | None = None
    codigo_origem: str | None = None
    id: int | None = None

    def __post_init__(self):
        obrigatorio(self.tag, "TAG")
        obrigatorio(self.denominacao, "denominação")


@dataclass(frozen=True)
class Medicao:
    codigo_evento: str
    equipamento_id: int
    tecnico_id: int
    solicitante_id: int
    parametro: str
    valor_nominal_mm: float
    tolerancia_inferior_mm: float
    tolerancia_superior_mm: float
    medida_1_mm: float
    medida_2_mm: float
    origem_registro: str
    status: str = "PENDENTE"
    id: int | None = None

    def __post_init__(self):
        for nome in ("codigo_evento", "parametro", "origem_registro"):
            obrigatorio(getattr(self, nome), nome)
        for nome in ("equipamento_id", "tecnico_id", "solicitante_id"):
            if type(getattr(self, nome)) is not int or getattr(self, nome) <= 0:
                raise ValueError(f"{nome}: identificador positivo obrigatório")
        for nome in ("valor_nominal_mm", "tolerancia_inferior_mm", "tolerancia_superior_mm",
                     "medida_1_mm", "medida_2_mm"):
            v = getattr(self, nome)
            if type(v) not in (int, float) or not math.isfinite(v):
                raise ValueError(f"{nome}: número finito obrigatório")
        if self.tolerancia_inferior_mm > self.tolerancia_superior_mm:
            raise ValueError("Afastamentos invertidos")
        if self.status not in {"PENDENTE", "EM_REVISAO", "VALIDADA", "EMITIDA"}:
            raise ValueError("Estado documental inválido")

    @staticmethod
    def _mm(n):
        return Decimal(str(n))

    @property
    def media(self):
        return (self._mm(self.medida_1_mm) + self._mm(self.medida_2_mm)) / 2

    @property
    def erro(self):
        return self.media - self._mm(self.valor_nominal_mm)

    @property
    def resultado(self):
        dentro = self._mm(self.tolerancia_inferior_mm) <= self.erro <= self._mm(self.tolerancia_superior_mm)
        return "APROVADO" if dentro else "REPROVADO"


class ErroPersistencia(RuntimeError):
    """Falha SQL traduzida para o chamador, com causa original preservada."""


class Banco:
    # Identificadores SQL são internos; todos os valores externos são vinculados com ?.
    _tabelas = {Tecnico: "tecnico_solicitante", Equipamento: "equipamento", Medicao: "medicao"}

    def __init__(self, caminho):
        self.caminho = caminho

    @contextmanager
    def conexao(self):
        con = None
        try:
            con = sqlite3.connect(self.caminho)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys = ON")
            with con:
                yield con
        except sqlite3.Error as exc:
            raise ErroPersistencia(str(exc)) from exc
        finally:
            if con is not None:
                con.close()

    def preparar(self):
        ddl = Path(__file__).with_name("03_banco.sql").read_text(encoding="utf-8-sig")
        with self.conexao() as c:
            c.executescript(ddl)

    def salvar(self, obj):
        tabela = self._tabelas[type(obj)]
        dados = {f.name: getattr(obj, f.name) for f in fields(obj) if f.name != "id"}
        if isinstance(obj, Medicao):
            dados.update(media_mm=float(obj.media), erro_mm=float(obj.erro))
        with self.conexao() as c:
            if isinstance(obj, Tecnico) and obj.id is not None:
                anterior = c.execute("SELECT papel FROM tecnico_solicitante WHERE id=?", (obj.id,)).fetchone()
                if anterior and anterior["papel"] != obj.papel:
                    raise ValueError("O papel do cadastro não pode ser alterado")
            if obj.id is None:
                marcas = ",".join("?" for _ in dados)
                return c.execute(f"INSERT INTO {tabela} ({','.join(dados)}) VALUES ({marcas})",
                                 tuple(dados.values())).lastrowid
            atribuicoes = ",".join(f"{nome}=?" for nome in dados)
            res = c.execute(f"UPDATE {tabela} SET {atribuicoes} WHERE id=?",
                            (*dados.values(), obj.id))
            if not res.rowcount:
                raise KeyError(obj.id)
            return obj.id

    def buscar(self, classe, codigo):
        with self.conexao() as c:
            linha = c.execute(f"SELECT * FROM {self._tabelas[classe]} WHERE id=?", (codigo,)).fetchone()
            if linha is None:
                raise KeyError(codigo)
            return classe(**{f.name: linha[f.name] for f in fields(classe)})

    def excluir(self, classe, codigo):
        with self.conexao() as c:
            if not c.execute(f"DELETE FROM {self._tabelas[classe]} WHERE id=?", (codigo,)).rowcount:
                raise KeyError(codigo)

    def relatorio(self, evento):
        with self.conexao() as c:
            linhas = c.execute("""
                SELECT m.*, e.tag, t.nome AS tecnico, s.nome AS solicitante
                FROM medicao m JOIN equipamento e ON e.id=m.equipamento_id
                JOIN tecnico_solicitante t ON t.id=m.tecnico_id
                JOIN tecnico_solicitante s ON s.id=m.solicitante_id
                WHERE m.codigo_evento=? ORDER BY m.id
            """, (evento,)).fetchall()
        for linha in linhas:
            med = Medicao(**{f.name: linha[f.name] for f in fields(Medicao)})
            yield med, linha["tag"], linha["tecnico"], linha["solicitante"]
