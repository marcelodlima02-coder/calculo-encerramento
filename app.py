import io
import openpyxl
from datetime import datetime
import streamlit as st
from fpdf import FPDF

def normalizar_texto(texto):
    if not texto:
        return "Nao informado"
    s = str(texto)
    subst = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Ç': 'C',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U'
    }
    for k, v in subst.items():
        s = s.replace(k, v)
    return s

def get_val(ws, r, c):
    return ws.cell(row=r, column=c).value

def format_date(val):
    if isinstance(val, datetime):
        return val.strftime('%d/%m/%Y')
    return str(val) if val else "Nao informado"

def format_money(val):
    if val is None or val == "":
        return "R$ 0,00"
    try:
        v = float(val)
        prefix = "-" if v < 0 else ""
        return f"{prefix}R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

st.set_page_config(page_title="Termo de Encerramento", page_icon="📄", layout="centered")

st.title("📄 Gerador de Termo de Encerramento de Contrato")
st.write("Upload da planilha de encerramento para cálculo automático e geração do PDF de acerto.")

file_excel = st.file_uploader("Selecione a Planilha de Encerramento (.xlsx)", type=["xlsx"])

if file_excel:
    if st.button("🚀 Gerar Termo em PDF", type="primary"):
        with st.spinner("Processando calculos e gerando o PDF..."):
            wb = openpyxl.load_workbook(file_excel, data_only=True)
            ws = wb["Planilha1"]
            
            # Dados do Contrato
            locador = normalizar_texto(get_val(ws, 4, 2))
            locatario = normalizar_texto(get_val(ws, 5, 2))
            imovel = normalizar_texto(get_val(ws, 6, 2))
            iptu_num = normalizar_texto(get_val(ws, 7, 2))
            
            aluguel = float(get_val(ws, 9, 2) or 0.0)
            dt_inicio_raw = get_val(ws, 14, 2)
            dt_fim_raw = get_val(ws, 15, 2)
            dt_rescisao_raw = get_val(ws, 15, 5)
            
            # 1. Multa Rescisoria
            tem_multa_raw = get_val(ws, 17, 2)
            flag_multa = str(tem_multa_raw).strip().upper() in ['1', 'S', 'SIM', 'TRUE']
            multa_calc = 0.0
            if flag_multa and isinstance(dt_inicio_raw, datetime) and isinstance(dt_fim_raw, datetime) and isinstance(dt_rescisao_raw, datetime):
                prazo_total = (dt_fim_raw - dt_inicio_raw).days
                tempo_decorrido = (dt_rescisao_raw - dt_inicio_raw).days
                dias_restantes = prazo_total - tempo_decorrido
                if prazo_total > 0 and dias_restantes > 0:
                    multa_calc = round(((aluguel * 3) / prazo_total) * dias_restantes, 2)

            # 2. Seguro Incendio Reembolso
            dt_incendio_inicio = get_val(ws, 12, 3)
            vlr_seguro_total = float(get_val(ws, 12, 5) or 0.0)
            reembolso_seguro_flag = str(get_val(ws, 13, 3)).strip().upper() in ['S', 'SIM', 'TRUE', '1']
            
            seguro_reembolso_calc = 0.0
            if reembolso_seguro_flag and isinstance(dt_incendio_inicio, datetime) and isinstance(dt_rescisao_raw, datetime) and vlr_seguro_total > 0:
                dias_efetivos = (dt_rescisao_raw - dt_incendio_inicio).days + 1
                if dias_efetivos > 0:
                    seguro_reembolso_calc = round((vlr_seguro_total / 365.0) * dias_efetivos * 0.8025, 2)

            # Itens Financeiros
            itens_financeiros = []
            total_debitos = 0.0
            
            for r in range(32, 42):
                nome = get_val(ws, r, 1)
                val = get_val(ws, r, 3)
                
                if r == 36 and flag_multa:
                    val = multa_calc
                
                if r == 37 and reembolso_seguro_flag and seguro_reembolso_calc > 0:
                    val = -seguro_reembolso_calc
                
                if val is not None and val != "" and float(val or 0) != 0 and nome is not None:
                    v_float = float(val)
                    total_debitos += v_float
                    itens_financeiros.append({
                        "nome": normalizar_texto(nome),
                        "valor_str": format_money(v_float)
                    })

            valor_caucao = float(get_val(ws, 42, 3) or 0.0) if ws.max_row >= 42 else 0.0
            saldo_final = total_debitos - valor_caucao
            
            # Geracao do PDF com FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Header
            pdf.set_font('Helvetica', 'B', 15)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 8, 'TERMO DE ENCERRAMENTO DE CONTRATO', 0, 1, 'C')
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(127, 140, 141)
            pdf.cell(0, 5, 'Resumo de Acerto Financeiro e Devolucao de Imovel', 0, 1, 'C')
            pdf.ln(4)
            pdf.set_draw_color(44, 62, 80)
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)
            
            # Secao 1: Dados do Contrato
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, ' DADOS DO CONTRATO', 0, 1, 'L', fill=True)
            pdf.ln(2)
            
            pdf.set_text_color(50, 50, 50)
            def add_row(label, val_str):
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(45, 6, label, 1, 0, 'L')
                pdf.set_font('Helvetica', '', 9)
                pdf.cell(145, 6, str(val_str), 1, 1, 'L')
                
            add_row('Locador:', locador)
            add_row('Locatario:', locatario)
            add_row('Imovel:', imovel)
            add_row('Inscricao IPTU/TLP:', iptu_num)
            pdf.ln(4)
            
            # Secao 2: Prazos e Datas
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, ' PRAZOS E DATAS', 0, 1, 'L', fill=True)
            pdf.ln(2)
            
            add_row('Inicio do Contrato:', format_date(dt_inicio_raw))
            add_row('Fim do Contrato:', format_date(dt_fim_raw))
            add_row('Data Rescisao/Chaves:', format_date(dt_rescisao_raw))
            pdf.ln(4)
            
            # Secao 3: Apuracao Financeira
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, ' APURACAO FINANCEIRA PARA ACERTO', 0, 1, 'L', fill=True)
            pdf.ln(2)
            
            pdf.set_text_color(50, 50, 50)
            for item in itens_financeiros:
                pdf.set_font('Helvetica', '', 9)
                pdf.cell(130, 6, item['nome'], 'B', 0, 'L')
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(60, 6, item['valor_str'], 'B', 1, 'R')
                
            if valor_caucao > 0:
                pdf.set_font('Helvetica', '', 9)
                pdf.cell(130, 6, '(-) Abatimento de Caucao Depositada', 'B', 0, 'L')
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(60, 6, f"-{format_money(valor_caucao)}", 'B', 1, 'R')
                
            pdf.ln(4)
            
            # Box Total Final
            if saldo_final > 0:
                label_tot = "VALOR A SER COBRADO DO LOCATARIO: "
                val_tot_str = format_money(saldo_final)
                fill_r, fill_g, fill_b = 245, 215, 215
            elif saldo_final < 0:
                label_tot = "VALOR A DEVOLVER AO LOCATARIO: "
                val_tot_str = format_money(abs(saldo_final))
                fill_r, fill_g, fill_b = 215, 245, 215
            else:
                label_tot = "ACERTO QUITADO: "
                val_tot_str = "R$ 0,00"
                fill_r, fill_g, fill_b = 230, 230, 230
                
            pdf.set_fill_color(fill_r, fill_g, fill_b)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(120, 10, label_tot, 0, 0, 'R', fill=True)
            pdf.cell(70, 10, val_tot_str + " ", 0, 1, 'R', fill=True)
            pdf.ln(10)
            
            # Declaracao de Quitacao
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 4, 'Declaro para os devidos fins que as chaves do imovel acima citado foram entregues nesta data, estando as partes de acordo com os valores apurados neste termo para a quitacao final das obrigacoes financeiras inerentes ao contrato de locacao.')
            pdf.ln(15)
            
            # Linhas de Assinatura
            y_sig = pdf.get_y()
            pdf.line(20, y_sig, 90, y_sig)
            pdf.line(110, y_sig, 180, y_sig)
            
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(50, 50, 50)
            pdf.text(25, y_sig + 5, str(locatario)[:30])
            pdf.text(42, y_sig + 9, 'Locatario')
            
            pdf.text(115, y_sig + 5, str(locador)[:30])
            pdf.text(125, y_sig + 9, 'Locador (ou Representante)')
            
            pdf_out = pdf.output(dest='S').encode('latin-1')

        st.success("✅ Termo em PDF gerado com sucesso!")
        
        st.download_button(
            label="📥 Baixar Termo de Encerramento (PDF)",
            data=pdf_out,
            file_name=f"Termo_Encerramento_{locatario.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
