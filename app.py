
 
import calendar
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

MONEDA = "$"
CATEGORIAS = [
    "Comida",
    "Transporte",
    "Ocio",
    "Servicios",
    "Educación",
    "Salud",
    "Otros",
]
COLUMNAS = ["fecha", "categoria", "monto", "descripcion"]

st.set_page_config(
    page_title="Control de Presupuesto Inteligente",
    page_icon="📊",
    layout="wide",
)


def fmt(x: float) -> str:
    return f"{MONEDA}{x:,.2f}"


if "gastos" not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=COLUMNAS)
if "presupuesto" not in st.session_state:
    st.session_state.presupuesto = 750.0

hoy = date.today()
dias_mes = calendar.monthrange(hoy.year, hoy.month)[1]
inicio_mes = date(hoy.year, hoy.month, 1)
fin_mes = date(hoy.year, hoy.month, dias_mes)


def datos_ejemplo() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    filas = []
    dia_libro = max(1, round(hoy.day * 0.7))

    for d in range(1, hoy.day + 1):
        f = date(hoy.year, hoy.month, d)
        filas.append((f, "Comida", round(float(rng.uniform(9, 15)), 2), "Almuerzo / comida diaria"))
        if rng.random() < 0.75:
            filas.append((f, "Transporte", round(float(rng.uniform(2, 5)), 2), "Transporte urbano"))
        if rng.random() < 0.35:
            filas.append((f, "Ocio", round(float(rng.uniform(5, 12)), 2), "Salida / recreación"))
        if rng.random() < 0.55:
            filas.append((f, "Educación", round(float(rng.uniform(3, 7)), 2), "Copias / materiales"))
        if d % 9 == 0:
            filas.append((f, "Servicios", round(float(rng.uniform(7, 11)), 2), "Internet / electricidad"))

    filas.append((date(hoy.year, hoy.month, dia_libro), "Educación", 85.0, "Libro de texto"))
    return pd.DataFrame(filas, columns=COLUMNAS)


with st.sidebar:
    st.markdown("## 🎯 Presupuesto mensual")
    st.session_state.presupuesto = st.number_input(
        f"Límite asignado ({MONEDA})",
        min_value=0.0,
        value=float(st.session_state.presupuesto),
        step=10.0,
    )

    st.divider()
    st.markdown("## 🧾 Nuevo movimiento")
    with st.form("form_gasto", clear_on_submit=True):
        f_fecha = st.date_input("Fecha", value=hoy, min_value=inicio_mes, max_value=fin_mes)
        f_cat = st.selectbox("Categoría", CATEGORIAS)
        f_monto = st.number_input(f"Monto ({MONEDA})", min_value=0.0, step=1.0, format="%.2f")
        f_desc = st.text_input("Descripción", placeholder="Ej. Compra en supermercado")
        enviado = st.form_submit_button("➕ Registrar gasto", use_container_width=True)

    if enviado:
        if f_monto <= 0:
            st.warning("⚠️ El monto debe ser mayor que 0.")
        else:
            desc_limpia = f_desc.strip() if f_desc.strip() else "Sin descripción"
            nueva = pd.DataFrame([(f_fecha, f_cat, float(f_monto), desc_limpia)], columns=COLUMNAS)
            st.session_state.gastos = pd.concat([st.session_state.gastos, nueva], ignore_index=True)
            st.toast("Gasto registrado correctamente", icon="✅")
            st.rerun()

    st.divider()
    st.markdown("## 🛠️ Controles")
    c1, c2 = st.columns(2)
    if c1.button("↩️ Deshacer", use_container_width=True, disabled=st.session_state.gastos.empty):
        st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
        st.rerun()
    if c2.button("🗑️ Limpiar", use_container_width=True, disabled=st.session_state.gastos.empty):
        st.session_state.gastos = pd.DataFrame(columns=COLUMNAS)
        st.rerun()

    if st.button("🧪 Cargar datos de demo", use_container_width=True):
        st.session_state.gastos = datos_ejemplo()
        st.rerun()

st.markdown("# 📊 Control de Presupuesto Inteligente")
st.caption(f"Período: **{calendar.month_name[hoy.month].capitalize()} {hoy.year}** · Duración: **{dias_mes} días**")

df = st.session_state.gastos.copy()
if df.empty:
    st.info("💡 Aún no hay registros. Agrega un gasto en el panel lateral o haz clic en **Cargar datos de demo**.")
    st.stop()

df["fecha"] = pd.to_datetime(df["fecha"])
df["monto"] = df["monto"].astype(float)
df = df[(df["fecha"].dt.year == hoy.year) & (df["fecha"].dt.month == hoy.month)]

if df.empty:
    st.info("💡 No existen gastos registrados dentro del mes en curso.")
    st.stop()

presupuesto = float(st.session_state.presupuesto)
total = float(df["monto"].sum())
disponible = presupuesto - total
porcentaje_uso = (total / presupuesto) if presupuesto > 0 else 0.0

ultimo_dia = int(max(hoy.day, df["fecha"].dt.day.max()))
restantes = dias_mes - ultimo_dia

diario = (
    df.groupby(df["fecha"].dt.day)["monto"]
    .sum()
    .reindex(range(1, ultimo_dia + 1), fill_value=0.0)
)
acumulado = diario.cumsum()

proyeccion = None
pendiente = intercepto = None
if ultimo_dia >= 2:
    x = np.arange(1, ultimo_dia + 1, dtype=float)
    pendiente, intercepto = np.polyfit(x, acumulado.values, 1)
    proyeccion = max(float(pendiente * dias_mes + intercepto), total)

m1, m2, m3, m4 = st.columns(4)
m1.metric("💳 Gastado a la fecha", fmt(total))
m2.metric("🎯 Presupuesto mensual", fmt(presupuesto))
m3.metric("💰 Saldo disponible", fmt(disponible), delta=fmt(disponible), delta_color="normal")
m4.metric(
    "🔮 Proyección cierre",
    fmt(proyeccion) if proyeccion is not None else "Sin datos",
    delta=fmt(presupuesto - proyeccion) if proyeccion is not None else None,
)

st.progress(min(max(porcentaje_uso, 0.0), 1.0))
st.caption(f"Has consumido el **{porcentaje_uso * 100:.1f}%** del presupuesto asignado.")

tab_resumen, tab_alertas, tab_detalle = st.tabs(
    ["📈 Proyección y Gráficas", "🚨 Detección de Atípicos", "📋 Libro de Gastos"]
)

with tab_resumen:
    st.markdown("### 🔮 Diagnóstico y proyección de cierre")
    if proyeccion is None:
        st.info("Se requieren al menos **2 días** con registro para estimar la tendencia del mes.")
    elif total > presupuesto:
        st.error(
            f"🚨 **Presupuesto excedido:** ya superaste el límite por **{fmt(total - presupuesto)}**. "
            f"A este ritmo, cerrarías el mes en **{fmt(proyeccion)}**."
        )
    elif proyeccion <= presupuesto:
        st.success(
            f"✅ **Ritmo saludable:** cerrarías el mes en **{fmt(proyeccion)}**, con un margen favorable de "
            f"**{fmt(presupuesto - proyeccion)}**."
        )
    else:
        exceso = proyeccion - presupuesto
        if restantes > 0:
            recorte = exceso / restantes
            permitido = max(disponible, 0.0) / restantes
            st.warning(
                f"⚠️ **Riesgo de sobregiro:** proyectas cerrar en **{fmt(proyeccion)}** "
                f"(**{fmt(exceso)}** por encima del presupuesto). Para ajustarte, reduce **{fmt(recorte)}/día** "
                f"en los **{restantes} días** restantes (tope sugerido: **{fmt(permitido)}/día**)."
            )
        else:
            st.warning(f"⚠️ Cerraste el mes **{fmt(exceso)}** por encima de tu presupuesto.")

    st.markdown("### 📉 Visualización financiera")
    g1, g2 = st.columns(2)

    with g1:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(acumulado.index),
                y=acumulado.values,
                mode="lines+markers",
                name="Acumulado real",
                line=dict(color="#4F8BF9", width=3),
            )
        )
        if proyeccion is not None and restantes > 0:
            fig.add_trace(
                go.Scatter(
                    x=[ultimo_dia, dias_mes],
                    y=[float(acumulado.iloc[-1]), proyeccion],
                    mode="lines",
                    name="Proyección lineal",
                    line=dict(color="#F5A623", width=3, dash="dash"),
                )
            )
        fig.add_hline(
            y=presupuesto,
            line_color="#EF4444",
            line_width=2,
            annotation_text="Presupuesto",
            annotation_position="top left",
        )
        fig.update_layout(
            template="plotly_dark",
            title="Gasto acumulado vs. proyección",
            xaxis_title="Día del mes",
            yaxis_title=f"Monto ({MONEDA})",
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h", y=-0.22),
        )
        fig.update_xaxes(range=[1, dias_mes])
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        por_cat = df.groupby("categoria")["monto"].sum().sort_values(ascending=True)
        fig2 = go.Figure(
            go.Bar(
                x=por_cat.values,
                y=por_cat.index,
                orientation="h",
                marker_color="#38BDF8",
                text=[fmt(v) for v in por_cat.values],
                textposition="auto",
            )
        )
        fig2.update_layout(
            template="plotly_dark",
            title="Distribución por categoría",
            xaxis_title=f"Total ({MONEDA})",
            margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab_alertas:
    st.markdown("### 🚨 Alertas de gastos inusuales")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📅 Días atípicos (Z-score modificado)")
        dias_con_gasto = diario[diario > 0]
        if len(dias_con_gasto) < 5:
            st.caption("Se necesitan al menos 5 días con gasto para aplicar este análisis.")
        else:
            med = dias_con_gasto.median()
            mad = (dias_con_gasto - med).abs().median()
            if mad > 0:
                z = 0.6745 * (dias_con_gasto - med) / mad
            else:
                mean_ad = (dias_con_gasto - med).abs().mean()
                z = (dias_con_gasto - med) / (1.253314 * mean_ad) if mean_ad > 0 else dias_con_gasto * 0

            raros = z[z > 3.5]
            if raros.empty:
                st.success("✅ No se detectan días con picos anormales.")
            else:
                tabla_dias = pd.DataFrame(
                    {
                        "Día": [date(hoy.year, hoy.month, int(d)).strftime("%d/%m") for d in raros.index],
                        "Gasto del día": [fmt(dias_con_gasto[d]) for d in raros.index],
                        "Mediana": fmt(med),
                        "Z modificado": [round(float(v), 1) for v in raros.values],
                    }
                )
                st.dataframe(tabla_dias, hide_index=True, use_container_width=True)

    with col_b:
        st.markdown("#### 🏷️ Gastos raros por categoría (Regla IQR)")
        hallazgos = []
        for cat, g in df.groupby("categoria"):
            if len(g) < 4:
                continue
            q1, q3 = g["monto"].quantile([0.25, 0.75])
            limite = q3 + 1.5 * (q3 - q1)
            for _, fila in g[g["monto"] > limite].iterrows():
                hallazgos.append(
                    {
                        "Fecha": fila["fecha"].strftime("%d/%m"),
                        "Categoría": cat,
                        "Monto": fmt(fila["monto"]),
                        "Límite IQR": fmt(limite),
                        "Descripción": fila["descripcion"],
                    }
                )

        if hallazgos:
            st.dataframe(pd.DataFrame(hallazgos), hide_index=True, use_container_width=True)
        else:
            st.success("✅ Todos los gastos están dentro del rango habitual de su categoría.")
        st.caption("Se evalúan categorías con al menos 4 registros.")

with tab_detalle:
    st.markdown("### 📋 Registro detallado del mes")
    vista = df.sort_values("fecha", ascending=False).copy()
    vista["fecha_fmt"] = vista["fecha"].dt.strftime("%d/%m/%Y")
    vista["monto_fmt"] = vista["monto"].apply(fmt)
    st.dataframe(
        vista[["fecha_fmt", "categoria", "monto_fmt", "descripcion"]].rename(
            columns={
                "fecha_fmt": "Fecha",
                "categoria": "Categoría",
                "monto_fmt": "Monto",
                "descripcion": "Descripción",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    csv_data = df.sort_values("fecha", ascending=False).to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar movimientos (CSV)",
        data=csv_data,
        file_name=f"gastos_{hoy.year}_{hoy.month:02d}.csv",
        mime="text/csv",
    )