import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, DoughnutChart, Reference
from openpyxl.utils import get_column_letter

# Crear libro de trabajo
wb = openpyxl.Workbook()

NAVY_HEADER = "002060"
BORDER_GREY = "D9D9D9"
TEXT_MAIN = "333333"
WHITE = "FFFFFF"

# 1. BASE DE DATOS
ws_bd = wb.active
ws_bd.title = "BD"

headers_bd = ["ID_Caso", "Fecha_Notificacion", "Ano", "Semana", "Provincia", "Region", 
              "Sexo", "Grupo_Edad", "Clasificacion_Final", "Tipo_Atencion", "Dias_Sintomas", "Defuncion"]

sample_data = [
    [1, "2026-01-10", 2026, 2, "Distrito Nacional", "Ozama", "Femenino", "20 29", "Confirmado", "Ambulatorio", 3, "No"],
    [2, "2026-01-11", 2026, 2, "Azua", "Valdesia", "Masculino", "30 39", "Sospechoso", "En domicilio", 4, "No"],
    [3, "2026-01-12", 2026, 2, "Baoruco", "Enriquillo", "Femenino", "10 19", "Descartado", "Ambulatorio", 2, "No"],
    [4, "2026-01-13", 2026, 2, "Barahona", "Enriquillo", "Masculino", "40 49", "Confirmado", "Internamiento", 6, "Si"],
    [5, "2026-01-14", 2026, 2, "Dajabón", "Noroeste", "Femenino", "50 59", "Probable", "Ambulatorio", 3, "No"],
    [6, "2026-01-15", 2026, 2, "Duarte", "Cibao Nordeste", "Masculino", "60 o más", "Confirmado", "Internamiento", 8, "Si"],
    [7, "2026-01-16", 2026, 2, "Elías Piña", "El Valle", "Femenino", "1 4", "Pendiente", "En domicilio", 2, "No"],
    [8, "2026-01-17", 2026, 2, "Distrito Nacional", "Ozama", "Masculino", "20 29", "Confirmado", "Ambulatorio", 4, "No"],
]

ws_bd.append(headers_bd)
for row in sample_data:
    ws_bd.append(row)

for col_num, header in enumerate(headers_bd, 1):
    cell = ws_bd.cell(row=1, column=col_num)
    cell.font = Font(name="Calibri", size=11, bold=True, color=WHITE)
    cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")

# 2. TABLAS AUXILIARES
ws_calc = wb.create_sheet(title="CALCULOS")

ws_calc["A1"] = "Clasificación"
ws_calc["B1"] = "Casos (en miles)"
labs_data = [["Descartado", 56.4], ["Pendiente", 12.1], ["Confirmado", 15.0], ["Sospechoso", 3.0], ["Probable", 0.5]]
for r_idx, row in enumerate(labs_data, start=2):
    ws_calc.cell(row=r_idx, column=1, value=row[0])
    ws_calc.cell(row=r_idx, column=2, value=row[1])

ws_calc["D1"] = "Síntoma"
ws_calc["E1"] = "Casos (en miles)"
sintomas_data = [["Fiebre", 31], ["ASINTOMÁTICO", 14], ["Dolor de cabeza", 6], ["Dolor de cabeza, Fiebre", 4], ["MALESTAR GENERAL", 4], ["FIEBRE, DOLOR DE CABEZA", 3]]
for r_idx, row in enumerate(sintomas_data, start=2):
    ws_calc.cell(row=r_idx, column=4, value=row[0])
    ws_calc.cell(row=r_idx, column=5, value=row[1])

ws_calc["G1"], ws_calc["H1"], ws_calc["I1"], ws_calc["J1"], ws_calc["K1"] = "Provincia", "Casos Total", "Confirmados", "Defunciones", "Tasa Letalidad (%)"
prov_data = [
    ["01 Distrito Nacional", 4437, 601, 200, 4.51],
    ["02 Azua", 24182, 70, 34, 0.14],
    ["03 Baoruco", 4276, 5, 18, 0.42],
    ["04 Barahona", 954, 8, 29, 3.04],
    ["05 Dajabón", 260, 71, 14, 5.38],
    ["06 Duarte", 1875, 200, 71, 3.79],
    ["07 Elías Piña", 2307, 14, 28, 1.21]
]
for r_idx, row in enumerate(prov_data, start=2):
    for c_idx, val in enumerate(row, start=7):
        ws_calc.cell(row=r_idx, column=c_idx, value=val)

# 3. DASHBOARD
ws_dash = wb.create_sheet(title="DASHBOARD")
ws_dash.views.sheetView[0].showGridLines = False

ws_dash.merge_cells("A1:Q2")
header_cell = ws_dash["A1"]
header_cell.value = "VIGILANCIA EPIDEMIOLÓGICA — DASHBOARD DE CASOS (MSP)"
header_cell.font = Font(name="Segoe UI", size=16, bold=True, color=WHITE)
header_cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
header_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)

def create_kpi_card(ws, start_col, start_row, end_col, end_row, title, val_str, var_str, bg_color):
    ws.merge_cells(start_row=start_row, start_column=start_col, end_row=end_row, end_column=end_col)
    top_left = ws.cell(row=start_row, column=start_col)
    top_left.value = f"{title}\n{val_str}\n{var_str}"
    top_left.font = Font(name="Segoe UI", size=10, bold=True, color=TEXT_MAIN)
    top_left.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    top_left.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    thin_border = Border(left=Side(style='thin', color=BORDER_GREY), right=Side(style='thin', color=BORDER_GREY),
                         top=Side(style='thin', color=BORDER_GREY), bottom=Side(style='thin', color=BORDER_GREY))
    for r in range(start_row, end_row + 1):
        for c in range(start_col, end_col + 1):
            ws.cell(row=r, column=c).border = thin_border

create_kpi_card(ws_dash, 3, 4, 5, 6, "Casos Notificados", "92,742 mil", "↓ -0,05 % Var", "E6F0FA")
create_kpi_card(ws_dash, 6, 4, 8, 6, "Casos Confirmados", "5,336 mil", "↑ 0,54 % Var", "E6F8E8")
create_kpi_card(ws_dash, 9, 4, 11, 6, "Casos Sospechosos", "123", "↑ 0,09 % Var", "FFF8E6")
create_kpi_card(ws_dash, 12, 4, 14, 6, "Casos Descartados", "1,235 mil", "↓ -0,60 % Var", "F2F2F2")
create_kpi_card(ws_dash, 15, 4, 17, 6, "Defunciones", "2,201 mil", "↓ -0,14 % Var", "FCE8E6")

# Gráfico de Anillo
chart_lab = DoughnutChart()
chart_lab.title = "Resultados de Laboratorio"
labels_lab = Reference(ws_calc, min_col=1, min_row=2, max_row=6)
data_lab = Reference(ws_calc, min_col=2, min_row=1, max_row=6)
chart_lab.add_data(data_lab, titles_from_data=True)
chart_lab.set_categories(labels_lab)
chart_lab.width, chart_lab.height = 12, 7.5
ws_dash.add_chart(chart_lab, "C8")

# Gráfico de Barras
chart_sintomas = BarChart()
chart_sintomas.type = "bar"
chart_sintomas.title = "Top Signos y Síntomas"
labels_sint = Reference(ws_calc, min_col=4, min_row=2, max_row=7)
data_sint = Reference(ws_calc, min_col=5, min_row=1, max_row=7)
chart_sintomas.add_data(data_sint, titles_from_data=True)
chart_sintomas.set_categories(labels_sint)
chart_sintomas.legend = None
chart_sintomas.width, chart_sintomas.height = 13, 7.5
ws_dash.add_chart(chart_sintomas, "J8")

# Tabla Resumen
start_r = 22
ws_dash.cell(row=start_r-1, column=3, value="Resumen por Provincia").font = Font(bold=True, size=11)
headers_prov_dash = ["Provincia", "Casos Total", "Casos Confirmados", "Defunciones", "Tasa Letalidad (%)"]
for c_idx, h in enumerate(headers_prov_dash, start=3):
    cell = ws_dash.cell(row=start_r, column=c_idx, value=h)
    cell.font = Font(name="Segoe UI", size=10, bold=True, color=WHITE)
    cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")

for row_idx, data_row in enumerate(prov_data, start=start_r+1):
    for col_idx, val in enumerate(data_row, start=3):
        cell = ws_dash.cell(row=row_idx, column=col_idx, value=val)
        cell.font = Font(name="Segoe UI", size=9)
        cell.border = Border(bottom=Side(style='thin', color=BORDER_GREY))

for ws in [ws_dash, ws_bd, ws_calc]:
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

# Guarda el archivo en la misma carpeta donde ejecutes este script
wb.save("Dashboard_Vigilancia_Epidemiologica_MSP.xlsx")
print("¡Archivo generado con éxito en tu carpeta actual!")