import io
from datetime import datetime, date
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

def format_money(val):
    if val is None or val == "":
        return "R$ 0,00"
    try:
        v = float(val)
        prefix = "-" if v < 0 else ""
        return f"{prefix}R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

st.set_page_config(page_title="Encerramento de Contrato", page_icon="📄", layout="wide")

st.title("📄 Painel de Encerramento de Contrato de Locação")
st.write("Preencha os dados abaixo para calcular os valores e gerar o Termo de Encerramento em PDF.")

# Form de Entrada de Dados com campos zerados e vazios
with st.form("form_encerramento"):
    st.subheader("1. Dados do Contrato e Partes")
    c1, c2 = st.columns(2)
    with c1:
        locador = st.text_input("Nome do Locador", value="", placeholder="Digite o nome do locador")
        imovel = st.text_input("Endereço do Imóvel", value="", placeholder="Digite o endereço completo do imóvel")
    with c2:
        locatario = st.text_input("Nome do Locatário", value="", placeholder="Digite o nome do locatário")
        iptu_num = st.text_input("Inscrição IPTU/TLP", value="", placeholder="Digite a inscrição do IPTU")

    st.subheader("2. Prazos e Aluguel Base")
    c3, c4, c5, c6 = st.columns(4)
    with c3:
        dt_inicio = st.date_input("Data Início Contrato", value=date.today())
    with c4:
        dt_fim = st.date_input("Data Fim Contrato", value=date.today())
    with c5:
        dt_rescisao = st.date_input("Data Rescisão / Chaves", value=date.today())
    with c6:
        aluguel = st.number_input("Valor do Último Aluguel (R$)", value=0.0, min_value=0.0, step=100.0)

    st.subheader("3. Regras de Condomínio e Multa")
    c7, c8, c9, c10 = st.columns(4)
    with c7:
        vlr_condominio = st.number_input("Valor Mensal Condomínio (R$)", value=0.0, min_value=0.0)
    with c8:
        tipo_condominio = st.selectbox("Tipo de Condomínio", ["Vincendo", "Vencido"])
    with c9:
        status_condominio = st.selectbox("Status Mês Rescisão", ["Pago", "Não Pago"])
    with c10:
        aplicar_multa = st.checkbox("Aplicar Multa Rescisória?", value=False)

    st.subheader("4. IPTU/TLP e Seguro Incêndio")
    c11, c12, c13, c14 = st.columns(4)
    with c11:
        iptu_anual = st.number_input("Valor IPTU+TLP Anual (R$)", value=0.0, min_value=0.0)
    with c12:
        iptu_pago = st.number_input("IPTU Já Pago Locatário (R$)", value=0.0, min_value=0.0)
    with c13:
        dt_seguro_inicio = st.date_input("Início Ciclo Seguro Incêndio", value=date.today())
    with c14:
        vlr_seguro_anual = st.number_input("Valor Seguro Anual (R$)", value=0.0, min_value=0.0)
    
    reembolso_seguro = st.checkbox("Reembolsar Seguro Incêndio Proporcional?", value=False)

    st.subheader("5. Reparos, Outros Lançamentos e Caução")
    c15, c16 = st.columns(2)
    with c15:
        vlr_reparos = st.number_input("Reparos / Danos Imóvel (R$)", value=0.0, min_value=0.0)
        desc_extra1 = st.text_input("Outros 1 - Descrição", value="", placeholder="Ex: Pintura")
        vlr_extra1 = st.number_input("Outros 1 - Valor (R$)", value=0.0, min_value=0.0)
        desc_extra2 = st.text_input("Outros 2 - Descrição", value="", placeholder="Ex: Troca de Fechadura")
        vlr_extra2 = st.number_input("Outros 2 - Valor (R$)", value=0.0, min_value=0.0)
    with c16:
        desc_extra3 = st.text_input("Outros 3 - Descrição", value="", placeholder="Ex: Limpeza")
        vlr_extra3_val = st.number_input("Outros 3 - Valor (R$)", value=0.0, min_value=0.0)
        vlr_caucao = st.number_input("Valor Caução Depositada (R$)", value=0.0, min_value=0.0)

    btn_calcular = st.form_submit_button("🚀 Calcular e Gerar Termo em PDF", type="primary")

# Processamento do Cálculo
if btn_calcular:
    dias_mes_saida = dt_rescisao.day
    
    # 1. Aluguel Proporcional (Mês comercial de 30 dias)
    aluguel_prop = round((aluguel / 30.0) * min(dias_mes_saida, 30), 2)
    
    # 2. Condomínio Proporcional
    vlr_dia_cond = vlr_condominio / 30.0
    dias_usufruidos = min(dias_mes_saida, 30)
    dias_nao_usufruidos = 30 - dias_usufruidos
    
    if tipo_condominio == "Vincendo":
        if status_condominio == "Pago":
            vlr_cond_calc = -round(vlr_dia_cond * dias_nao_usufruidos, 2)
        else:
            vlr_cond_calc = round(vlr_dia_cond * dias_usufruidos, 2)
    else: # Vencido
        if status_condominio == "Pago":
            vlr_cond_calc = round(vlr_dia_cond * dias_usufruidos, 2)
        else:
            vlr_cond_calc = round(vlr_condominio + (vlr_dia_cond * dias_usufruidos), 2)

    # 3. IPTU Proporcional
    dt_inicio_ano = date(dt_rescisao.year, 1, 1)
    dias_iptu = (dt_rescisao - dt_inicio_ano).days + 1
    iptu_devido_ano = (iptu_anual / 365.0) * dias_iptu
    iptu_prop = round(iptu_devido_ano - iptu_pago, 2)

    # 4. Multa Rescisória
    multa_calc = 0.0
    if aplicar_multa:
        prazo_total = (dt_fim - dt_inicio).days
        tempo_decorrido = (dt_rescisao - dt_inicio).days
        dias_restantes = prazo_total - tempo_decorrido
        if prazo_total > 0 and dias_restantes > 0:
            multa_calc = round(((aluguel * 3.0) / prazo_total) * dias_restantes, 2)

    # 5. Seguro Incêndio
    seguro_reembolso_calc = 0.0
    if reembolso_seguro and dt_seguro_inicio and vlr_seguro_anual > 0:
        dias_efetivos = (dt_rescisao - dt_seguro_inicio).days + 1
        if dias_efetivos > 0:
            seguro_reembolso_calc = round((vlr_seguro_anual / 365.0) * dias_efetivos * 0.8025, 2)

    # Lista de Itens para o PDF
    itens_financeiros = []
    
    if aluguel_prop > 0:
        itens_financeiros.append({"nome": "Aluguel proporcional mes corrente", "valor": aluguel_prop})
    if vlr_cond_calc != 0:
        nome_cond = "Reembolso Condominio Proporcional (Vincendo)" if vlr_cond_calc < 0 else "Condominio Proporcional"
        itens_financeiros.append({"nome": nome_cond, "valor": vlr_cond_calc})
    if iptu_prop != 0:
        itens_financeiros.append({"nome": "IPTU/TLP Proporcional", "valor": iptu_prop})
    if multa_calc > 0:
        itens_financeiros.append({"nome": "Multa Rescisoria Contratual", "valor": multa_calc})
    if seguro_reembolso_calc > 0:
        itens_financeiros.append({"nome": "Reembolso Seguro Incendio Proporcional", "valor": -seguro_reembolso_calc})
    if vlr_reparos > 0:
        itens_financeiros.append({"nome": "Reparos / Danos no Imovel", "valor": vlr_reparos})
    if vlr_extra1 > 0:
        itens_financeiros.append({"nome": desc_extra1 or "Outros Lancamentos 1", "valor": vlr_extra1})
    if vlr_extra2 > 0:
        itens_financeiros.append({"nome": desc_extra2 or "Outros Lancamentos 2", "valor": vlr_extra2})
    if vlr_extra3_val > 0:
        itens_financeiros.append({"nome": desc_extra3 or "Outros Lancamentos 3", "valor": vlr_extra3_val})

    total_debitos = sum(item["valor"] for item in itens_financeiros)
    saldo_final = total_debitos - vlr_caucao

    # Resumo na Tela
    st.markdown("---")
    st.subheader("📊 Resumo do Acerto Calculado")
    for item in itens_financeiros:
        st.write(f"• **{item['nome']}**: {format_money(item['valor'])}")
    if vlr_caucao > 0:
        st.write(f"• **(-) Abatimento de Caução**: -{format_money(vlr_caucao)}")

    if saldo_final > 0:
        st.error(f"**VALOR A SER COBRADO DO LOCATÁRIO: {format_money(saldo_final)}**")
    elif saldo_final < 0:
        st.success(f"**VALOR A DEVOLVER AO LOCATÁRIO: {format_money(abs(saldo_final))}**")
    else:
        st.info("**ACERTO QUITADO: R$ 0,00**")

    # Geração do PDF
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
    
    # Seção 1
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
        
    add_row('Locador:', normalizar_texto(locador))
    add_row('Locatario:', normalizar_texto(locatario))
    add_row('Imovel:', normalizar_texto(imovel))
    add_row('Inscricao IPTU/TLP:', normalizar_texto(iptu_num))
    pdf.ln(4)
    
    # Seção 2
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, ' PRAZOS E DATAS', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    add_row('Inicio do Contrato:', dt_inicio.strftime('%d/%m/%Y'))
    add_row('Fim do Contrato:', dt_fim.strftime('%d/%m/%Y'))
    add_row('Data Rescisao/Chaves:', dt_rescisao.strftime('%d/%m/%Y'))
    pdf.ln(4)
    
    # Seção 3
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, ' APURACAO FINANCEIRA PARA ACERTO', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_text_color(50, 50, 50)
    for item in itens_financeiros:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(130, 6, normalizar_texto(item['nome']), 'B', 0, 'L')
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(60, 6, format_money(item['valor']), 'B', 1, 'R')
        
    if vlr_caucao > 0:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(130, 6, '(-) Abatimento de Caucao Depositada', 'B', 0, 'L')
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(60, 6, f"-{format_money(vlr_caucao)}", 'B', 1, 'R')
        
    pdf.ln(4)
    
    # Box Total
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
    
    # Declaração
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, 'Declaro para os devidos fins que as chaves do imovel acima citado foram entregues nesta data, estando as partes de acordo com os valores apurados neste termo para a quitacao final das obrigacoes financeiras inerentes ao contrato de locacao.')
    pdf.ln(15)
    
    # Assinaturas
    y_sig = pdf.get_y()
    pdf.line(20, y_sig, 90, y_sig)
    pdf.line(110, y_sig, 180, y_sig)
    
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(50, 50, 50)
    pdf.text(25, y_sig + 5, normalizar_texto(locatario)[:30])
    pdf.text(42, y_sig + 9, 'Locatario')
    
    pdf.text(115, y_sig + 5, normalizar_texto(locador)[:30])
    pdf.text(125, y_sig + 9, 'Locador (ou Representante)')
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    st.download_button(
        label="📥 Baixar Termo de Encerramento em PDF",
        data=pdf_bytes,
        file_name=f"Termo_Encerramento_{normalizar_texto(locatario).replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
