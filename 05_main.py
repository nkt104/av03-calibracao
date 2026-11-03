"""Demonstração: python 05_main.py (ou --banco caminho.sqlite)."""
import argparse
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

dom = import_module("04_classes")


def demonstrar(caminho):
    banco = dom.Banco(caminho)
    banco.preparar()
    evento = "DEMO-" + uuid4().hex
    tecnico = banco.salvar(dom.Tecnico("Técnica " + evento, "0007", "Metrologia"))
    solicitante = banco.salvar(dom.Tecnico("Setor " + evento, setor="Usinagem", papel="SOLICITANTE"))
    equipamento = banco.salvar(dom.Equipamento("DC-" + evento, "Dispositivo didático"))
    modelo = dom.Medicao(evento, equipamento, tecnico, solicitante, "Diâmetro A",
                         10, -0.05, 0.05, 10.02, 10.04, "Demonstração sintética / par A")
    primeiro = banco.salvar(modelo)
    banco.salvar(replace(modelo, parametro="Diâmetro B", medida_1_mm=10.06, medida_2_mm=10.08,
                         origem_registro="Demonstração sintética / par B"))
    # Consulta e atualização real: enviar o primeiro resultado à revisão documental.
    banco.salvar(replace(banco.buscar(dom.Medicao, primeiro), status="EM_REVISAO"))
    print("RELATÓRIO DE CALIBRAÇÃO | Dados fictícios | Unidade: mm")
    print(f"Evento: {evento}")
    for m, tag, t, s in banco.relatorio(evento):
        print(f"{m.parametro} | TAG: {tag} | Técnico: {t} | Solicitante: {s}")
        print(f"  Leituras: {m.medida_1_mm:.3f}; {m.medida_2_mm:.3f} | Média: {m.media:.3f}"
              f" | Erro: {m.erro:+.3f} | Faixa do erro: [{m.tolerancia_inferior_mm:+.3f}, {m.tolerancia_superior_mm:+.3f}]")
        print(f"  Resultado do ensaio: {m.resultado} | Estado documental: {m.status}")
    print("Demonstração acadêmica; este relatório não é um certificado emitido.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", type=Path, help="Preservar os dados nesse arquivo SQLite.")
    args = parser.parse_args()
    try:
        if args.banco:
            demonstrar(args.banco)
        else:
            with TemporaryDirectory() as pasta:
                demonstrar(Path(pasta) / "demo.sqlite")
    except (dom.ErroPersistencia, OSError, ValueError) as erro:
        parser.exit(1, f"Falha na demonstração: {erro}\n")
