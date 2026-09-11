import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def generar_grafico_composicion(comp):
        labels = ['Sindical', 'Seg. Social', 'Obra Social', 'INSSJP', 'ART', 'SCVO']
        valores = [
            float(comp.composicion_total_sindical),
            float(comp.composicion_total_seg_social),
            float(comp.composicion_total_obra_social),
            float(comp.composicion_total_inssjp),
            float(comp.composicion_total_art),
            float(comp.composicion_total_scvo),
        ]

        # sacar valores nulos
        labels_filtrados = [l for l, v in zip(labels, valores) if v > 0]
        valores_filtrados = [v for v in valores if v > 0]

        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(valores_filtrados, labels=labels_filtrados, autopct='%1.1f%%')
        # ax.set_title('Composición de cargas')

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)

        imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return imagen_base64