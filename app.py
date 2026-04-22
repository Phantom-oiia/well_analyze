import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Настройка страницы ---
st.set_page_config(page_title="Анализ оттока клиентов", layout="wide")
st.title("📊 Универсальный анализатор оттока клиентов")

# --- Котик-приветствие ---
st.markdown("### Привет, дружок Я — твой аналитик-котик 🐾")
st.image("https://cataas.com/cat/says/Загрузи%20файл", width=300, caption="Готов к анализу!")

st.markdown("""
Загрузите CSV-файл с данными о клиентах — и узнайте, почему они уходят.  
Поддерживается русский и английский язык.
""")

# --- Загрузка файла ---
uploaded_file = st.file_uploader("📁 Загрузите CSV-файл", type="csv")

if uploaded_file is not None:
    try:
        # Читаем файл
        df = pd.read_csv(uploaded_file)
        st.success("✅ Файл загружен успешно!")
        st.image("https://cataas.com/cat/cute", width=200, caption="О, интересные данные!")
        st.write("### Первые строки данных:")
        st.dataframe(df.head())

        # --- Автоопределение столбцов ---
        def detect_col(df, keywords):
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    return col
            return None

        col_churn = detect_col(df, ['churn', 'отток', 'ушёл', '流失'])
        col_tenure = detect_col(df, ['tenure', 'месяц', 'срок', 'длительность'])
        col_charge = detect_col(df, ['charge', 'плат', 'cost', 'оплата'])
        col_contract = detect_col(df, ['contract', 'договор', 'тариф'])

        if not col_churn:
            st.error("❌ Не найден столбец с информацией об оттоке (например, Churn)")
            st.image("https://cataas.com/cat/sad", width=200, caption="Не могу помочь без данных об оттоке...")
            st.stop()

        # --- Преобразуем Churn в 0/1 ---
        def normalize_churn(val):
            val = str(val).strip().lower()
            if val in ['1', 'yes', 'да', 'true', 'ушёл', '流失']:
                return 1
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
        contract_data = None
        if col_contract:
            contract_data = df[col_contract].astype(str)
            contract_summary = contract_data.groupby(churn_data).value_counts().unstack(fill_value=0)

        # --- Вывод графиков ---
        st.write("### 📈 Результаты анализа")
        st.image("https://cataas.com/cat/working", width=180, caption="Котик строит графики...")

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
        if col_contract and 'contract_summary' in locals() and not contract_summary.empty:
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

        # --- Вывод интерпретации ---
        st.write("### 💡 Выводы")
        st.write(f"- Всего клиентов: **{len(df)}**")
        st.write(f"- Ушло: **{churn_count}** ({churn_rate:.1%})")

        if churn_rate > 0.3:
            st.warning("⚠️ Высокий отток Рассмотрите меры удержания.")
            st.image("https://cataas.com/cat/sad", width=200, caption="Ой-ой... давайте сохраним клиентов!")
        else:
            st.success("✅ Уровень оттока в норме.")
            st.image("https://cataas.com/cat/happy", width=200, caption="Котик доволен 😸")

        if avg_churn_charge and avg_stay_charge:
            if avg_churn_charge > avg_stay_charge:
                diff = (avg_churn_charge - avg_stay_charge) / avg_stay_charge * 100
                st.warning(f"💸 Ушедшие платили на **{diff:.1f}% больше** — возможно, цена отпугивает.")
                st.image("https://cataas.com/cat/money", width=200, caption="Дорого — не значит круто!")
            else:
                st.info("💳 Платежи не являются причиной оттока.")
                st.image("https://cataas.com/cat/check", width=200, caption="Цены в порядке!")

        if col_contract:
            st.info(f"📌 Совет: клиенты с месячным контрактом чаще уходят — предложите скидку за долгосрочную подписку.")
            st.image("https://cataas.com/cat/dance", width=200, caption="Подписка — и котик танцует!")

    except Exception as e:
        st.error(f"❌ Ошибка при обработке файла: {e}")
        st.image("https://cataas.com/cat/angry", width=200, caption="Что-то пошло не так...")
else:
    st.info("👈 Загрузите CSV-файл, чтобы начать анализ.")
    st.image("https://cataas.com/cat/sleep", width=200, caption="Котик ждёт файл...")
