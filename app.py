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
st.write("Preencha os dados abaixo para calcular os valores, visualizar a prévia na tela e gerar o Termo em PDF.")

# Form de Entrada de Dados
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
        dt_inicio = st.date_input("Data Início Contrato", value=None, format="DD/MM/YYYY", key="dt_inicio")
    with c4:
        dt_fim = st.date_input("Data Fim Contrato", value=None, format="DD/MM/YYYY", key="dt_fim")
    with c5:
        dt_rescisao = st.date_input("Data Rescisão / Chaves", value=None, format="DD/MM/YYYY", key="dt_rescisao")
    with c6:
        aluguel = st.number_input("Valor do Último Aluguel (R$)", value=0.0, min_value=0.0, step=100.0)

    st.subheader("3. Regras de Aluguel Proporcional, Condomínio e Multa")
    c7, c8, c9, c10 = st.columns(4)
    with c7:
        tipo_aluguel = st.selectbox("Tipo do Aluguel", ["Vencido", "Vincendo"])
    with c8:
        status_aluguel = st.selectbox("Status Aluguel Mês Rescisão", ["Pago", "Não Pago"])
    with c9:
        modelo_ciclo_aluguel = st.selectbox("Modelo do Ciclo do Aluguel", ["Mês Fechado (01 a 30)", "Por Ciclo de Vencimento"])
    with c10:
        dia_vencimento_aluguel = st.number_input("Dia de Vencimento do Aluguel", value=5, min_value=1, max_value=31, step=1, help="Utilizado quando o ciclo não for Mês Fechado")

    st.markdown("---")
    c11, c12, c13, c14 = st.columns(4)
    with c11:
        vlr_condominio = st.number_input("Valor Mensal Condomínio (R$)", value=0.0, min_value=0.0)
    with c12:
        tipo_condominio = st.selectbox("Tipo de Condomínio", ["Vincendo", "Vencido"])
    with c13:
        status_condominio = st.selectbox("Status Condomínio Mês Rescisão", ["Pago", "Não Pago"])
    with c14:
        aplicar_multa = st.checkbox("Aplicar Multa Rescisória?", value=False)

    st.subheader("4. IPTU/TLP e Seguro Incêndio")
    c15, c16 = st.columns(2)
    with c15:
        iptu_anual = st.number_input("Valor IPTU+TLP Anual (R$)", value=0.0, min_value=0.0)
    with c16:
        iptu_pago = st.number_input("IPTU Já Pago Locatário (R$)", value=0.0, min_value=0.0)

    st.markdown("---")
    st.write("**Seguro Incêndio**")
    cal_seguro = st.checkbox("Calcular Reembolso / Cobrança de Seguro Incêndio?", value=False)
    
    c17, c18, c19 = st.columns(3)
    with c17:
        dt_seguro_inicio = st.date_input("Início do Ciclo do Seguro", value=None, format="DD/MM/YYYY", key="dt_seg_inicio")
    with c18:
        vlr_seguro_anual = st.number_input("Valor Seguro Anual (R$)", value=0.0, min_value=0.0)
    with c19:
        vlr_seguro_pago = st.number_input("Valor Seguro Pago pelo Locatário (R$)", value=0.0, min_value=0.0)

    st.subheader("5. Reparos, Outros Lançamentos e Caução")
    c20, c21 = st.columns(2)
    with c20:
        vlr_reparos = st.number_input("Reparos / Danos Imóvel (R$)", value=0.0, min_value=0.0)
        desc_extra1 = st.text_input("Outros 1 - Descrição", value="", placeholder="Ex: Pintura")
        vlr_extra1 = st.number_input("Outros 1 - Valor (R$)", value=0.0, min_value=0.0)
        desc_extra2 = st.text_input("Outros 2 - Descrição", value="", placeholder="Ex: Troca de Fechadura")
        vlr_extra2 = st.number_input("Outros 2 - Valor (R$)", value=0.0, min_value=0.0)
    with c21:
        desc_extra3 = st.text_input("Outros 3 - Descrição", value="", placeholder="Ex: Limpeza")
        vlr_extra3_val = st.number_input("Outros 3 - Valor (R$)", value=0.0, min_value=0.0)
        vlr_caucao = st.number_input("Valor Caução Depositada (R$)", value=0.0, min_value=0.0)

    btn_calcular = st.form_submit_button("🚀 Calcular e Visualizar Acerto", type="primary")

# Processamento do Cálculo
if btn_calcular:
    if not dt_rescisao:
        st.warning("⚠️ Por favor, selecione a Data de Rescisão / Chaves para realizar os cálculos.")
    else:
        dia_saida = dt_rescisao.day
        itens_financeiros = []
        
        # 1. Aluguel Proporcional
        eh_mes_fechado = (modelo_ciclo_aluguel == "Mês Fechado (01 a 30)")
        val_dia_aluguel = aluguel / 30.0
        
        if eh_mes_fechado:
            dias_ocupados_aluguel = min(dia_saida, 30)
            dias_nao_usufruidos_aluguel = 30 - dias_ocupados_aluguel
        else:
            if dia_saida >= dia_vencimento_aluguel:
                dias_ocupados_aluguel = dia_saida - dia_vencimento_aluguel
                dias_nao_usufruidos_aluguel = 30 - dias_ocupados_aluguel
            else:
                dias_ocupados_aluguel = (30 - dia_vencimento_aluguel) + dia_saida
                dias_nao_usufruidos_aluguel = dia_vencimento_aluguel - dia_saida

        if tipo_aluguel == "Vincendo":
            if status_aluguel == "Pago":
                dias_reembolso_vincendo = 30 - min(dia_saida, 30)
                val_aluguel_calc = -round(val_dia_aluguel * dias_reembolso_vincendo, 2)
                if val_aluguel_calc < 0:
                    itens_financeiros.append({"nome": "Reembolso Aluguel Proporcional (Vincendo)", "valor": val_aluguel_calc})
            else:
                val_aluguel_calc = round(val_dia_aluguel * min(dia_saida, 30), 2)
                if val_aluguel_calc > 0:
                    itens_financeiros.append({"nome": "Aluguel Proporcional Mes Encerramento", "valor": val_aluguel_calc})
        else: # Vencido
            if status_aluguel == "Pago":
                if dia_saida < dia_vencimento_aluguel and not eh_mes_fechado:
                    val_aluguel_calc = -round(val_dia_aluguel * dias_nao_usufruidos_aluguel, 2)
                    if val_aluguel_calc < 0:
                        itens_financeiros.append({"nome": "Reembolso Aluguel Proporcional (Vencido)", "valor": val_aluguel_calc})
                else:
                    val_aluguel_calc = round(val_dia_aluguel * dias_ocupados_aluguel, 2)
                    if val_aluguel_calc > 0:
                        itens_financeiros.append({"nome": "Aluguel Proporcional Mes Encerramento", "valor": val_aluguel_calc})
            else:
                if dia_saida >= dia_vencimento_aluguel or eh_mes_fechado:
                    vlr_aluguel_mes_ant = round(aluguel, 2)
                    vlr_aluguel_prop = round(val_dia_aluguel * dias_ocupados_aluguel, 2)
                    if vlr_aluguel_mes_ant > 0:
                        itens_financeiros.append({"nome": "Aluguel Mes Anterior (Vencido)", "valor": vlr_aluguel_mes_ant})
                    if vlr_aluguel_prop > 0:
                        itens_financeiros.append({"nome": "Aluguel Proporcional Mes Encerramento", "valor": vlr_aluguel_prop})
                else:
                    val_aluguel_calc = round(val_dia_aluguel * dias_ocupados_aluguel, 2)
                    if val_aluguel_calc > 0:
                        itens_financeiros.append({"nome": "Aluguel Proporcional Mes Encerramento", "valor": val_aluguel_calc})

        # 2. Condomínio Proporcional
        vlr_dia_cond = vlr_condominio / 30.0
        dias_usufruidos_cond = min(dia_saida, 30)
        dias_nao_usufruidos_cond = 30 - dias_usufruidos_cond
        
        if tipo_condominio == "Vincendo":
            if status_condominio == "Pago":
                vlr_cond_calc = -round(vlr_dia_cond * dias_nao_usufruidos_cond, 2)
                if vlr_cond_calc < 0:
                    itens_financeiros.append({"nome": "Reembolso Condominio Proporcional (Vincendo)", "valor": vlr_cond_calc})
            else:
                vlr_cond_calc = round(vlr_dia_cond * dias_usufruidos_cond, 2)
                if vlr_cond_calc > 0:
                    itens_financeiros.append({"nome": "Condominio Proporcional", "valor": vlr_cond_calc})
        else: # Vencido
            if status_condominio == "Pago":
                vlr_cond_calc = round(vlr_dia_cond * dias_usufruidos_cond, 2)
                if vlr_cond_calc > 0:
                    itens_financeiros.append({"nome": "Condominio Proporcional", "valor": vlr_cond_calc})
            else:
                vlr_mes_anterior_cond = round(vlr_condominio, 2)
                vlr_prop_atual_cond = round(vlr_dia_cond * dias_usufruidos_cond, 2)
                
                if vlr_mes_anterior_cond > 0:
                    itens_financeiros.append({"nome": "Condominio Mes Anterior (Vencido)", "valor": vlr_mes_anterior_cond})
                if vlr_prop_atual_cond > 0:
                    itens_financeiros.append({"nome": "Condominio Proporcional Mes Encerramento", "valor": vlr_prop_atual_cond})

        # 3. IPTU Proporcional
        dt_inicio_ano = date(dt_rescisao.year, 1, 1)
        dias_iptu = (dt_rescisao - dt_inicio_ano).days + 1
        iptu_devido_ano = (iptu_anual / 365.0) * dias_iptu
        iptu_prop = round(iptu_devido_ano - iptu_pago, 2)
        if iptu_prop != 0:
            itens_financeiros.append({"nome": "IPTU/TLP Proporcional", "valor": iptu_prop})

        # 4. Multa Rescisória
        multa_calc = 0.0
        if aplicar_multa:
            if isinstance(dt_inicio, (date, datetime)) and isinstance(dt_fim, (date, datetime)):
                d_in = dt_inicio.date() if isinstance(dt_inicio, datetime) else dt_inicio
                d_fi = dt_fim.date() if isinstance(dt_fim, datetime) else dt_fim
                d_re = dt_rescisao.date() if isinstance(dt_rescisao, datetime) else dt_rescisao
                
                prazo_total = (d_fi - d_in).days
                tempo_decorrido = (d_re - d_in).days
                dias_restantes = prazo_total - tempo_decorrido
                
                if prazo_total > 0 and dias_restantes > 0:
                    multa_calc = round(((aluguel * 3.0) / prazo_total) * dias_restantes, 2)
                    if multa_calc > 0:
                        itens_financeiros.append({"nome": "Multa Rescisoria Contratual", "valor": multa_calc})
            else:
                st.warning("⚠️ Para calcular a Multa Rescisória, informe também as Datas de Início e Fim do Contrato.")

        # 5. Seguro Incêndio
        if cal_seguro and dt_seguro_inicio and vlr_seguro_anual > 0:
            d_seg_in = dt_seguro_inicio.date() if isinstance(dt_seguro_inicio, datetime) else dt_seguro_inicio
            d_re = dt_rescisao.date() if isinstance(dt_rescisao, datetime) else dt_rescisao
            dias_seguro = (d_re - d_seg_in).days
            if dias_seguro >= 0:
                vlr_devido_bruto = (vlr_seguro_anual / 365.0) * dias_seguro
                diferenca_seguro = vlr_devido_bruto - vlr_seguro_pago
                resultado_seguro = round(diferenca_seguro * 0.8025, 2)
                
                if resultado_seguro < 0:
                    itens_financeiros.append({"nome": "Reembolso Seguro Incendio Proporcional", "valor": resultado_seguro})
                elif resultado_seguro > 0:
                    itens_financeiros.append({"nome": "Cobranca Seguro Incendio Proporcional", "valor": resultado_seguro})

        # Reparos e Outros Lançamentos Extras
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

        # Prévia na Tela com Parâmetros de Auditagem
        st.markdown("---")
        st.subheader("📋 Relatório de Conferência e Auditoria de Dados")
        
        with st.expander("📌 Ver Todos os Dados e Parâmetros Digitados pelo Funcionário", expanded=True):
            st.markdown("##### 1. Dados do Contrato e Prazos")
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.write(f"• **Locador:** {locador or 'Não informado'}")
                st.write(f"• **Locatário:** {locatario or 'Não informado'}")
                st.write(f"• **Imóvel:** {imovel or 'Não informado'}")
                st.write(f"• **Inscrição IPTU:** {iptu_num or 'Não informado'}")
            with col_a2:
                st.write(f"• **Início Contrato:** {dt_inicio.strftime('%d/%m/%Y') if dt_inicio else 'Não informado'}")
                st.write(f"• **Fim Contrato:** {dt_fim.strftime('%d/%m/%Y') if dt_fim else 'Não informado'}")
                st.write(f"• **Data Rescisão:** {dt_rescisao.strftime('%d/%m/%Y') if dt_rescisao else 'Não informado'}")
            with col_a3:
                st.write(f"• **Aluguel Base:** {format_money(aluguel)}")
                st.write(f"• **Tipo / Status Aluguel:** {tipo_aluguel} | {status_aluguel}")
                st.write(f"• **Ciclo Aluguel:** {modelo_ciclo_aluguel} (Venc. Dia {dia_vencimento_aluguel})")

            st.markdown("##### 2. Condomínio, IPTU e Seguro Incêndio")
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                st.write(f"• **Condomínio Mensal:** {format_money(vlr_condominio)}")
                st.write(f"• **Tipo / Status Condomínio:** {tipo_condominio} | {status_condominio}")
                st.write(f"• **Multa Rescisória Aplicada:** {'Sim' if aplicar_multa else 'Não'}")
            with col_b2:
                st.write(f"• **IPTU Anual:** {format_money(iptu_anual)}")
                st.write(f"• **IPTU Já Pago pelo Locatário:** {format_money(iptu_pago)}")
            with col_b3:
                if cal_seguro:
                    st.write(f"• **Seguro Incêndio (Ciclo Início):** {dt_seguro_inicio.strftime('%d/%m/%Y') if dt_seguro_inicio else 'Não informado'}")
                    st.write(f"• **Seguro Anual:** {format_money(vlr_seguro_anual)}")
                    st.write(f"• **Seguro Pago pelo Locatário:** {format_money(vlr_seguro_pago)}")
                else:
                    st.write("• **Seguro Incêndio:** Não calculado")

            st.markdown("##### 3. Outros Lançamentos e Caução")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.write(f"• **Reparos / Danos:** {format_money(vlr_reparos)}")
                if vlr_extra1 > 0: st.write(f"• **{desc_extra1 or 'Outros 1'}:** {format_money(vlr_extra1)}")
                if vlr_extra2 > 0: st.write(f"• **{desc_extra2 or 'Outros 2'}:** {format_money(vlr_extra2)}")
                if vlr_extra3_val > 0: st.write(f"• **{desc_extra3 or 'Outros 3'}:** {format_money(vlr_extra3_val)}")
            with col_c2:
                st.write(f"• **Caução Depositada:** {format_money(vlr_caucao)}")

        st.markdown("---")
        st.subheader("📊 Prévia do Resultado Financeiro Apurado")
        
        col_esq, col_dir = st.columns([2, 1])
        
        with col_esq:
            st.markdown("#### Detalhamento das Rubricas")
            for item in itens_financeiros:
                st.write(f"• **{item['nome']}**: `{format_money(item['valor'])}`")
            if vlr_caucao > 0:
                st.write(f"• **(-) Abatimento de Caução Depositada**: `-{format_money(vlr_caucao)}`")

        with col_dir:
            st.markdown("#### Resultado Final")
            if saldo_final > 0:
                st.error(f"### VALOR A COBRAR\n## {format_money(saldo_final)}")
            elif saldo_final < 0:
                st.success(f"### VALOR A DEVOLVER\n## {format_money(abs(saldo_final))}")
            else:
                st.info("### ACERTO QUITADO\n## R$ 0,00")

        st.markdown("---")
        st.write("🔍 **Revise os valores acima.** Se estiver tudo correto, clique no botão abaixo para baixar o Termo oficial em PDF:")

        # PDF
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
        
        # Função auxiliar para tabela no PDF com redefinição explícita da cor do texto
        def add_pdf_row(label, val_str):
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(60, 6, normalizar_texto(label), 1, 0, 'L')
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(130, 6, normalizar_texto(val_str), 1, 1, 'L')

        # Seção 1
        pdf.set_fill_color(44, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, ' DADOS DO CONTRATO', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        add_pdf_row('Locador:', locador)
        add_pdf_row('Locatario:', locatario)
        add_pdf_row('Imovel:', imovel)
        add_pdf_row('Inscricao IPTU/TLP:', iptu_num)
        pdf.ln(4)
        
        # Seção 2
        pdf.set_fill_color(44, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, ' PRAZOS E DATAS', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        add_pdf_row('Inicio do Contrato:', dt_inicio.strftime('%d/%m/%Y') if dt_inicio else "Nao informado")
        add_pdf_row('Fim do Contrato:', dt_fim.strftime('%d/%m/%Y') if dt_fim else "Nao informado")
        add_pdf_row('Data Rescisao/Chaves:', dt_rescisao.strftime('%d/%m/%Y') if dt_rescisao else "Nao informado")
        pdf.ln(4)

        # Seção 3 - AUDITORIA DE PARÂMETROS DIGITADOS
        pdf.set_fill_color(44, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, ' PARAMETROS E DADOS INFORMADOS PARA O CALCULO', 0, 1, 'L', fill=True)
        pdf.ln(2)

        add_pdf_row('Aluguel Base / Tipo / Status:', f"{format_money(aluguel)} | {tipo_aluguel} | {status_aluguel}")
        add_pdf_row('Modelo Ciclo Aluguel:', f"{modelo_ciclo_aluguel} (Vencimento Dia {dia_vencimento_aluguel})")
        add_pdf_row('Condominio Mensal / Tipo / Status:', f"{format_money(vlr_condominio)} | {tipo_condominio} | {status_condominio}")
        add_pdf_row('IPTU Anual / Já Pago pelo Locatário:', f"{format_money(iptu_anual)} | {format_money(iptu_pago)}")
        if cal_seguro:
            dt_seg_str = dt_seguro_inicio.strftime('%d/%m/%Y') if dt_seguro_inicio else "Nao informado"
            add_pdf_row('Seguro Incendio (Inicio / Anual / Pago):', f"Inicio {dt_seg_str} | Anual {format_money(vlr_seguro_anual)} | Pago {format_money(vlr_seguro_pago)}")
        else:
            add_pdf_row('Seguro Incendio:', 'Nao Calculado')
        add_pdf_row('Multa Rescisoria Aplicada:', 'Sim' if aplicar_multa else 'Nao')
        pdf.ln(4)
        
        # Seção 4 - APURAÇÃO FINANCEIRA
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
        
        pdf_out = pdf.output()
        if isinstance(pdf_out, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_out)
        else:
            pdf_bytes = pdf.output(dest='S').encode('latin-1')

        st.download_button(
            label="📥 Baixar Termo de Encerramento em PDF",
            data=pdf_bytes,
            file_name=f"Termo_Encerramento_{normalizar_texto(locatario).replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
