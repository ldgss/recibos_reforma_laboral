import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def generar_grafico_composicion(comp):
    labels = ['Sindical', 'Seg. Social', 'Obra Social', 'INSSJP', 'ART', 'SCVO']
    colores = [
        "#dc0918",  # Sindical
        "#cc005a",  # Seg. Social
        "#9e3082",  # Obra Social
        "#62478c",  # INSSJP
        "#334d79",  # ART
        "#2f4858",  # SCVO
    ]
    valores = [
        float(comp.composicion_total_sindical),
        float(comp.composicion_total_seg_social),
        float(comp.composicion_total_obra_social),
        float(comp.composicion_total_inssjp),
        float(comp.composicion_total_art),
        float(comp.composicion_total_scvo),
    ]

    # sacar valores nulos (labels, valores y colores en paralelo)
    filtrados = [(l, v, c) for l, v, c in zip(labels, valores, colores) if v > 0]
    labels_filtrados = [f[0] for f in filtrados]
    valores_filtrados = [f[1] for f in filtrados]
    colores_filtrados = [f[2] for f in filtrados]

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, texts, autotexts = ax.pie(
        valores_filtrados,
        labels=labels_filtrados,
        colors=colores_filtrados,
        autopct='%1.1f%%',
        wedgeprops={"edgecolor": "black", "linewidth": 0.5},
    )

    # porcentajes legibles según el fondo de cada porción
    for at, c in zip(autotexts, colores_filtrados):
        r, g, b = [int(c[i:i+2], 16) for i in (1, 3, 5)]
        at.set_color("white" if (r*0.299 + g*0.587 + b*0.114) < 140 else "black")

    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8')