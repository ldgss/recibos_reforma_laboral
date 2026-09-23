from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
import graficador
import base64

with open("static/img/logo6.png", "rb") as f:
    logo_img = base64.b64encode(f.read()).decode("utf-8")

class Empresa():
    nombre = "Solvencia S.A."
    cuit = "30-70859171-8"
    localidad = "San Carlos"
    domicilio = "La Salada y Diamante"
    logo = logo_img

class Empleado():

    def __init__(self, datos):
        self.legajo = datos["legajo"]
        self.nombre = datos["nombre"]
        self.cuil = datos["cuil"]
        self.dni = str(datos["dni"]).strip()[3:-2]
        self.obra_social = str(datos["obra_social"])[13:-2] if datos["obra_social"] else '-'
        self.ingreso = self.format_date(datos["ingreso"])
        self.categoria = datos["categoria"]
        self.ingreso_reconocido = self.format_date(datos["ingreso_reconocido"])
        self.egreso = self.validar_egreso(datos["egreso"], datos["fin_contrato"])
        self.tipo_liquidacion = "Mensual" if "mensual" in str(datos["tipo_liquidacion"]).lower() else "Jornal"
        self.convenio = datos["convenio"]
        self.sueldo_bruto_categoria = datos["sueldo_bruto_categoria"][0] if datos["sueldo_bruto_categoria"] else None
        self.valor_bruto_categoria = datos["valor_bruto_categoria"][0] if datos["valor_bruto_categoria"] else None
        self.periodo = f'{str(datos["periodo"]).strip().split(' ')[0]} {str(datos["periodo"]).strip().split(' ')[1]}'
        self.pago = datos["pago"]
        self.fecha_pago_aportes = datos["fecha_pago_aportes"]

    def format_date(self, f):
        fecha = datetime.strptime(str(f), '%Y-%m-%d %H:%M:%S')
        resultado = fecha.strftime('%d-%m-%Y')
        return resultado 

    def validar_egreso(self, f_egreso, f_fin_contrato):
        limite = datetime.strptime('2040-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        fecha_egreso = datetime.strptime(str(f_egreso), '%Y-%m-%d %H:%M:%S')
        fecha_fin_contrato = datetime.strptime(str(f_fin_contrato), '%Y-%m-%d %H:%M:%S')

        if fecha_egreso < limite:
            return fecha_egreso.strftime('%d-%m-%Y')
        elif fecha_fin_contrato < limite:
            return fecha_fin_contrato.strftime('%d-%m-%Y')
        else:
            return '-'

class Recibo():

    def __init__(self, empresa, empleado, costo, sueldo, paginas):
        self.empresa = empresa
        self.empleado = empleado
        self.costo = costo
        self.sueldo = sueldo
        self.paginas = paginas
        self.monto_en_letras = self.monto_en_letras(sueldo.neto)
        self.costo_total_empleador = costo.costo_empleador + sueldo.remunerativo + sueldo.no_remunerativo
        self.composicion_total_sindical = costo.composicion.composicion_sindical_empleador + sueldo.composicion.composicion_sindical_trabajador
        self.composicion_total_seg_social = costo.composicion.composicion_seg_social_empleador + sueldo.composicion.composicion_seg_social_trabajador
        self.composicion_total_obra_social = costo.composicion.composicion_obra_social_empleador + sueldo.composicion.composicion_obra_social_trabajador
        self.composicion_total_inssjp = costo.composicion.composicion_inssjp_empleador + sueldo.composicion.composicion_inssjp_trabajador
        self.composicion_total_art = costo.composicion.composicion_art_empleador + sueldo.composicion.composicion_art_trabajador
        self.composicion_total_scvo = costo.composicion.composicion_scvo_empleador + sueldo.composicion.composicion_scvo_trabajador
        self.distribucion = graficador.generar_grafico_composicion(self)

    def monto_en_letras(self, monto):
        monto = Decimal(monto).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        entero = int(monto)
        centavos = int((monto - entero) * 100)
        texto_entero = num2words(entero, lang='es').upper()
        return f"SON PESOS {texto_entero} CON {centavos:02d}/100"

class Costo_empleador():

    CODIGOS_COSTOS_EMPLEADOR = ["con010", "con020", "con031", "con032", "con034", "con036"]

    def __init__(self):
        self.conceptos = []
        self.subtotal_costo_empleador = Decimal('0')
        self.costo_empleador = Decimal('0')
        self.composicion = Composicion_costo_salarial()


    def agregar(self, conceptos):
        for concepto in conceptos:
            if str(concepto["codigo"]).lower().strip() in self.CODIGOS_COSTOS_EMPLEADOR: 
                concepto_costo = Concepto_costo_empleador(concepto)
                self.conceptos.append(concepto_costo)
                self.subtotal_costo_empleador += Decimal(concepto_costo.monto)
                self.costo_empleador += Decimal(concepto_costo.monto)

                if str(concepto["codigo"]).lower().strip() == 'con034':
                    self.composicion.composicion_sindical_empleador += Decimal(concepto_costo.monto)
                if str(concepto["codigo"]).lower().strip() == 'con010':
                    self.composicion.composicion_seg_social_empleador += Decimal(concepto_costo.monto)
                if str(concepto["codigo"]).lower().strip() == 'con020':
                    self.composicion.composicion_obra_social_empleador += Decimal(concepto_costo.monto)
                if str(concepto["codigo"]).lower().strip() == 'con032':
                    self.composicion.composicion_art_empleador += Decimal(concepto_costo.monto)
                if str(concepto["codigo"]).lower().strip() == 'con036':
                    self.composicion.composicion_scvo_empleador += Decimal(concepto_costo.monto)

    def subtotal(self):
        return "subtotal"

    def total(self):
        return "total"

class Concepto_costo_empleador():

    def __init__(self, concepto):
        self.codigo = concepto["codigo"]
        self.denominacion = concepto["denominacion"]
        self.denominacion_recibo = concepto["denominacion_recibo"]
        self.denominacion_auxiliar = concepto["denominacion_auxiliar"]
        self.codigo_imputable = concepto["codigo_imputable"]
        self.tipo_concepto = concepto["tipo_concepto"]
        self.orden_calculo = concepto["orden_calculo"]
        self.orden = concepto["orden"]
        self.col_rec = concepto["col_rec"]
        self.um = concepto["um"]
        self.cantidad = concepto["cantidad"]
        self.monto = concepto["monto"]
        self.monto_recibo = concepto["monto_recibo"]

class Sueldo_bruto_empleado():

    CODIGOS_SUELDO_BRUTO = ["habcre", "habsre", "ret"]

    def __init__(self):
        self.conceptos = []
        self.bruto = Decimal('0')
        self.neto = Decimal('0')
        self.remunerativo = Decimal('0')
        self.no_remunerativo = Decimal('0')
        self.retenciones = Decimal('0')
        self.composicion = Composicion_costo_salarial()
        

    def agregar(self, conceptos):
        for concepto in conceptos:
            if str(concepto["tipo_concepto"]).lower().strip() in self.CODIGOS_SUELDO_BRUTO:
                concepto_sueldo = Concepto_sueldo_bruto_empleado(concepto)
                self.conceptos.append(concepto_sueldo)
                tipo_concepto = str(concepto_sueldo.tipo_concepto).lower().strip()
                if tipo_concepto == self.CODIGOS_SUELDO_BRUTO[0]:
                    self.remunerativo += Decimal(concepto_sueldo.monto)
                elif tipo_concepto == self.CODIGOS_SUELDO_BRUTO[1]:
                    self.no_remunerativo += Decimal(concepto_sueldo.monto)
                elif tipo_concepto == self.CODIGOS_SUELDO_BRUTO[2]:
                    self.retenciones += Decimal(concepto_sueldo.monto)

                if str(concepto["codigo"]).lower().strip() == 'ret030':
                    self.composicion.composicion_sindical_trabajador += Decimal(concepto_sueldo.monto)
                if str(concepto["codigo"]).lower().strip() == 'ret034':
                    self.composicion.composicion_sindical_trabajador += Decimal(concepto_sueldo.monto)
                if str(concepto["codigo"]).lower().strip() == 'ret010':
                    self.composicion.composicion_seg_social_trabajador += Decimal(concepto_sueldo.monto)
                if str(concepto["codigo"]).lower().strip() == 'ret020':
                    self.composicion.composicion_obra_social_trabajador += Decimal(concepto_sueldo.monto)
                if str(concepto["codigo"]).lower().strip() == 'ret016':
                    self.composicion.composicion_inssjp_trabajador += Decimal(concepto_sueldo.monto)

        self.neto = self.remunerativo + self.no_remunerativo - self.retenciones
        self.bruto = self.remunerativo + self.no_remunerativo

    def sueldo_bruto(self):
        return "sueldo bruto"

    def sueldo_neto(self):
        return "sueldo neto"

class Concepto_sueldo_bruto_empleado():

    def __init__(self, concepto):
        self.codigo = concepto["codigo"]
        self.denominacion = concepto["denominacion"]
        self.denominacion_recibo = concepto["denominacion_recibo"]
        self.denominacion_auxiliar = concepto["denominacion_auxiliar"]
        self.codigo_imputable = concepto["codigo_imputable"]
        self.tipo_concepto = concepto["tipo_concepto"]
        self.orden_calculo = concepto["orden_calculo"]
        self.orden = concepto["orden"]
        self.col_rec = concepto["col_rec"]
        self.um = concepto["um"]
        self.cantidad = concepto["cantidad"]
        self.monto = concepto["monto"]
        self.monto_recibo = concepto["monto_recibo"]

class Composicion_costo_salarial():

    def __init__(self):
        self.composicion_sindical_empleador = Decimal('0')
        self.composicion_sindical_trabajador = Decimal('0')
        self.composicion_seg_social_empleador = Decimal('0')
        self.composicion_seg_social_trabajador = Decimal('0')
        self.composicion_obra_social_empleador = Decimal('0')
        self.composicion_obra_social_trabajador = Decimal('0')
        self.composicion_inssjp_empleador = Decimal('0')
        self.composicion_inssjp_trabajador = Decimal('0')
        self.composicion_art_empleador = Decimal('0')
        self.composicion_art_trabajador = Decimal('0')
        self.composicion_scvo_empleador = Decimal('0')
        self.composicion_scvo_trabajador = Decimal('0')

class Distribucion_costo_grafico():

    def __init__(self, sindical, seguridad_social,
                     obra_social, INSSJP, ART, SCVO,
                     sueldo_neto):
            self.sindical = sindical
            self.seguridad_social = seguridad_social
            self.obra_social = obra_social
            self.INSSJP = INSSJP
            self.ART = ART
            self.SCVO = SCVO
            self.sueldo_neto = sueldo_neto

if __name__ == "__main__":
    print("Uso: python recibos.py recibos_listado.xlsx recibos_para_firmar.pdf")

