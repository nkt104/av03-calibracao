import unittest
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory

d = import_module("04_classes")


class TestMVP(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.b = d.Banco(Path(self.tmp.name) / "teste.sqlite")
        self.b.preparar()
        self.t = self.b.salvar(d.Tecnico("Técnico", "0007"))
        self.s = self.b.salvar(d.Tecnico("Setor", papel="SOLICITANTE"))
        self.e = self.b.salvar(d.Equipamento("TAG-1", "Controle"))
        self.m = d.Medicao("EV1", self.e, self.t, self.s, "Dimensão", 10, -.05, .05, 10.03, 10.07, "teste")

    def test_limites_inclusivos_e_fora_em_ambos_lados(self):
        for a,b,esperado in [(10.03,10.07,"APROVADO"),(9.95,9.95,"APROVADO"),
                             (9.94,9.95,"REPROVADO"),(10.05,10.06,"REPROVADO")]:
            with self.subTest(a=a,b=b):
                self.assertEqual(replace(self.m, medida_1_mm=a, medida_2_mm=b).resultado, esperado)

    def test_dados_invalidos(self):
        for mudanca in [{"medida_1_mm":float("nan")},{"medida_2_mm":None},{"tolerancia_inferior_mm":.06}]:
            with self.assertRaises(ValueError):
                replace(self.m, **mudanca)

    def test_crud_e_join(self):
        codigo = self.b.salvar(self.m)
        m = self.b.buscar(d.Medicao, codigo)
        self.b.salvar(replace(m, medida_2_mm=10.09, status="EM_REVISAO"))
        m, tag, tecnico, solicitante = next(self.b.relatorio("EV1"))
        self.assertEqual((m.resultado, m.status, tag, tecnico, solicitante),
                         ("REPROVADO","EM_REVISAO","TAG-1","Técnico","Setor"))
        with self.b.conexao() as c:
            row=c.execute("SELECT media_mm,erro_mm FROM medicao").fetchone()
            self.assertAlmostEqual(row[0],10.06)
            self.assertAlmostEqual(row[1],.06)
        self.b.excluir(d.Medicao,codigo)
        with self.assertRaises(KeyError):
            self.b.buscar(d.Medicao,codigo)

    def test_integridade_e_rollback(self):
        self.b.salvar(self.m)
        for obj in [self.m, replace(self.m, equipamento_id=999, parametro="X"),
                    replace(self.m, tecnico_id=self.s, parametro="X")]:
            with self.assertRaises(d.ErroPersistencia):
                self.b.salvar(obj)
        with self.assertRaises(d.ErroPersistencia):
            self.b.excluir(d.Equipamento,self.e)
        self.assertEqual(len(list(self.b.relatorio("EV1"))),1)

    def test_cadastros(self):
        for cls, codigo, ajuste in [(d.Tecnico,self.t,{"nome":"Ana"}),
                                    (d.Equipamento,self.e,{"denominacao":"Dispositivo B"})]:
            obj=self.b.buscar(cls,codigo)
            self.b.salvar(replace(obj,**ajuste))
            self.assertEqual(self.b.buscar(cls,codigo),replace(obj,**ajuste))
            self.b.excluir(cls,codigo)
            with self.assertRaises(KeyError):
                self.b.buscar(cls,codigo)
