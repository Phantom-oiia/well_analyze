import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
from datetime import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="ChurnCat 🐱", layout="wide")
st.markdown("<h1 style='text-align: center;'>📊 ChurnCat: Анализ оттока без кода</h1>", unsafe_allow_html=True)

# --- Выбор языка ---
lang = st.selectbox("🌐 Язык", ["Русский", "English", "中文"], key="lang_select")
texts = {
    "Русский": {
        "upload": "Загрузите CSV или Excel",
        "success": "✅ Файл загружен!",
        "churn_rate": "Ушло: **{count}** ({rate:.1%})",
        "high_churn": "⚠️ Высокий отток",
        "low_churn": "✅ Уровень оттока в норме",
        "price_issue": "💸 Ушедшие платили на **{diff:.1f}% больше**",
        "price_ok": "💳 Платежи не являются причиной оттока",
        "contract_tip": "📌 Совет: клиенты с месячным контрактом чаще уходят — предложите скидку за годовую оплату.",
        "age_info": "Средний возраст ушедших: **{age:.1f}** лет",
        "gender_info": "Пол ушедших: **{gender}**",
        "region_info": "Чаще уходят из: **{region}**",
        "export": "📤 Экспортировать отчёт",
        "disclaimer": "🔒 Данные не сохраняются. Анализ происходит в памяти.",
        "recommendation": "💡 Рекомендация",
        "loyalty": "Запустите программу лояльности для клиентов с высоким риском.",
        "discount": "Предложите скидку на продление — цена может быть барьером.",
        "contract_offer": "Предложите бонус за годовую подписку.",
    },
    "English": {
        "upload": "Upload CSV or Excel",
        "success": "✅ File uploaded!",
        "churn_rate": "Churned: **{count}** ({rate:.1%})",
        "high_churn": "⚠️ High churn",
        "low_churn": "✅ Churn rate is normal",
        "price_issue": "💸 Churned users paid **{diff:.1f}% more**",
        "price_ok": "💳 Payments are not the issue",
        "contract_tip": "📌 Tip: monthly plan users churn more — offer a discount for annual.",
        "age_info": "Avg age of churned: **{age:.1f}**",
        "gender_info": "Gender: **{gender}**",
        "region_info": "Most churn from: **{region}**",
        "export": "📤 Export report",
        "disclaimer": "🔒 Data is not saved. Analysis happens in memory.",
        "recommendation": "💡 Recommendation",
        "loyalty": "Launch a loyalty program for high-risk clients.",
        "discount": "Offer a renewal discount — price may be a barrier.",
        "contract_offer": "Offer a bonus for annual subscription.",
    },
    "中文": {
        "upload": "上传 CSV 或 Excel",
        "success": "✅ 文件已上传！",
        "churn_rate": "已流失：**{count}** ({rate:.1%})",
        "high_churn": "⚠️ 流失率过高",
        "low_churn": "✅ 流失率正常",
        "price_issue": "💸 流失客户支付了多 **{diff:.1f}%**",
        "price_ok": "💳 付款不是问题",
        "contract_tip": "📌 建议：月度合同客户更易流失 — 提供年度折扣",
        "age_info": "流失客户平均年龄：**{age:.1f}** 岁",
        "gender_info": "性别：**{gender}**",
        "region_info": "主要流失地区：**{region}**",
        "export": "📤 导出报告",
        "disclaimer": "🔒 数据不会被保存。分析在内存中进行。",
        "recommendation": "💡 建议",
        "loyalty": "为高风险客户推出忠诚度计划。",
        "discount": "提供续费折扣 — 价格可能是障碍。",
        "contract_offer": "为年度订阅提供奖励。",
    }
}
t = texts[lang]

# --- Загрузка файла ---
uploaded_file = st.file_uploader(t["upload"], type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Определяем тип файла
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
            st.success("📖 Загружен Excel-файл")
        else:
            df = pd.read_csv(uploaded_file)
            st.success("📄 Загружен CSV-файл")

        st.info(t["disclaimer"])
        st.write("### 📊 Первые строки данных:")
        st.dataframe(df.head())

        # --- Функция поиска столбца ---
        def detect_col(df, keywords):
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    return col
            return None

        # --- Определяем ключевые столбцы ---
        col_churn = detect_col(df, ['churn', 'отток', 'ушёл', '流失', '客户流失', 'status'])
        col_charge = detect_col(df, ['charge', 'плат', 'cost', 'оплата', 'payment', '费用'])
        col_contract = detect_col(df, ['contract', 'договор', 'tariff', '合同', 'plan'])
        col_age = detect_col(df, ['age', 'возраст', '年龄'])
        col_gender = detect_col(df, ['gender', 'пол', '性别'])
        col_region = detect_col(df, ['region', 'регион', '地区', 'city'])

        if not col_churn:
            st.error("❌ Не найден столбец с информацией об оттоке (например, Churn)")
            st.stop()

        # --- Нормализуем Churn ---
        def normalize_churn(val):
            val = str(val).strip().lower()
            if val in ['1', 'yes', 'да', 'true', 'ушёл', '流失', '是']:
                return 1
            if val in ['0', 'no', 'нет', 'false', 'остался', '正常', '否']:
                return 0
            return 0

        churn_data = df[col_churn].apply(normalize_churn)
        churn_count = churn_data.sum()
        stay_count = len(churn_data) - churn_count
        churn_rate = churn_count / len(churn_data) if len(churn_data) > 0 else 0

        # --- Средний платёж ---
        avg_churn_charge = None
        avg_stay_charge = None
        if col_charge:
            charges = pd.to_numeric(df[col_charge], errors='coerce')
            avg_churn_charge = charges[churn_data == 1].mean()
            avg_stay_charge = charges[churn_data == 0].mean()

        # --- Отток по контрактам ---
        contract_summary = None
        if col_contract:
            contract_data = df[col_contract].astype(str)
            contract_summary = contract_data.groupby(churn_data).value_counts().unstack(fill_value=0)

        # --- Графики ---
        st.write("### 📈 Результаты анализа")

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        # 1. Отток — столбцы
        axes[0].bar(['Остались', 'Ушли'], [stay_count, churn_count], color=['#2ECC71', '#E74C3C'], edgecolor='black')
        axes[0].set_title('Количество клиентов')
        axes[0].set_ylabel('Число')
        axes[0].grid(axis='y', alpha=0.3)

        # 2. Доля оттока
        axes[1].pie([stay_count, churn_count], labels=['Остались', 'Ушли'], autopct='%1.1f%%', colors=['#2ECC71', '#E74C3C'])
        axes[1].set_title('Доля оттока')

        # 3. Средний платёж
        if avg_churn_charge and avg_stay_charge:
            axes[2].bar(['Остались', 'Ушли'], [avg_stay_charge, avg_churn_charge], color=['#2ECC71', '#E74C3C'], alpha=0.8)
            axes[2].set_title('Средний платёж')
            axes[2].set_ylabel('₽')
            axes[2].grid(axis='y', alpha=0.3)
        else:
            axes[2].text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=axes[2].transAxes)
            axes[2].set_title('Средний платёж')

        # 4. Отток по контрактам
        if contract_summary is not None and not contract_summary.empty:
            contract_summary.T.plot(kind='bar', ax=axes[3], color=['#3498DB', '#E74C3C'], alpha=0.8)
            axes[3].set_title('Отток по типу контракта')
            axes[3].set_ylabel('Число клиентов')
            axes[3].grid(axis='y', alpha=0.3)
            axes[3].legend(['Остались', 'Ушли'])
        else:
            axes[3].text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=axes[3].transAxes)
            axes[3].set_title('Отток по контрактам')

        plt.suptitle("Анализ оттока клиентов", fontsize=16, fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig)

        # --- Дополнительный анализ ---
        st.write("### 🔍 Дополнительные инсайты")

        if col_age:
            avg_age_churn = df[col_age][churn_data == 1].mean()
            st.write(t["age_info"].format(age=avg_age_churn))

        if col_gender:
            gender_churn = df[col_gender][churn_data == 1].value_counts().idxmax()
            st.write(t["gender_info"].format(gender=gender_churn))

        if col_region:
            region_churn = df[col_region][churn_data == 1].value_counts().idxmax()
            st.write(t["region_info"].format(region=region_churn))

        # --- Рекомендации ---
        st.write("### 💡 Рекомендации")
        if churn_rate > 0.3:
            st.warning(t["high_churn"])
            st.markdown(f"**{t['recommendation']}:** {t['loyalty']}")
        else:
            st.success(t["low_churn"])

        if avg_churn_charge and avg_stay_charge and avg_churn_charge > avg_stay_charge:
            diff = (avg_churn_charge - avg_stay_charge) / avg_stay_charge * 100
            st.warning(t["price_issue"].format(diff=diff))
            st.markdown(f"**{t['recommendation']}:** {t['discount']}")
        else:
            st.info(t["price_ok"])

        if col_contract:
            st.info(t["contract_tip"])
            st.markdown(f"**{t['recommendation']}:** {t['contract_offer']}")

        # --- Экспорт отчёта ---
        st.write("### 📤 Экспорт отчёта")
        if st.button(t["export"]):
            from io import BytesIO
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()

            html = f"""
            <h1>Отчёт: Анализ оттока</h1>
            <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>{t['churn_rate'].format(count=churn_count, rate=churn_rate)}</p>
            <img src="data:image/png;base64,{img_base64}" />
            <h3>Рекомендации</h3>
            <ul>
                <li>{t['loyalty']}</li>
                <li>{t['discount']}</li>
                <li>{t['contract_offer']}</li>
            </ul>
            <p><em>Сгенерировано: ChurnCat 🐱</em></p>
            """
            b64 = base64.b64encode(html.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="churn_report.html">📥 Скачать отчёт (HTML)</a>'
            st.markdown(href, unsafe_allow_html=True)

        # --- Котик прощается ---
        st.markdown("---")
        st.markdown("<p style='text-align: center; font-style: italic;'>😼 Котик Мурлыч говорит: спасибо за данные. Мяу.</p>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Ошибка при обработке файла: {e}")
else:
    st.info("👈 Загрузите файл, чтобы начать анализ.")
    st.markdown("<p style='text-align: center;'>🐱 <em>Котик ждёт ваш CSV или Excel...</em></p>", unsafe_allow_html=True)
