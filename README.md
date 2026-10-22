# GenAI Data Warehouse & Business Insights Dashboard

A data warehousing and business analytics project that transforms Superstore sales data into meaningful business insights using Python, MySQL, Streamlit, and Generative AI.

## Project Overview

This project integrates data preprocessing, dimensional data modeling, SQL-based analysis, interactive visualizations, and AI-powered business insights into a single dashboard.

It helps users understand sales performance, profitability, customer segments, product categories, and regional business trends.

## Features

- **Interactive Dashboard:** Explore key sales and profit metrics.
- **Data Mining Insights:** Analyze customer segments and business performance.
- **Data Warehouse & ETL:** Prepare, clean, transform, and organize sales data for analysis.
- **MySQL Integration:** Store and query structured warehouse data.
- **GenAI Business Assistant:** Generate business insights using the Gemini API.
- **Data Visualization:** Present analytical results through interactive charts.

## Technologies Used

- Python
- MySQL
- Streamlit
- Pandas
- Plotly
- SQLAlchemy
- PyMySQL
- Google Gemini API

## Project Structure

```text
GenAI-Data-Warehouse/
├── Main_Dashboard.py
├── pages/
│   ├── 2_Data_Mining_Insights.py
│   ├── 3_Data_Warehouse_ETL.py
│   └── 4_GenAI_Business_Assistant.py
├── data/
├── customer_segmentation.py
├── prepare_data.py
├── load_data.py
├── check_data.py
├── requirements.txt
└── .gitignore
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shakti-git07/GenAI-Data-Warehouse.git
cd GenAI-Data-Warehouse
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and configure your own credentials:

```text
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=genai_data_warehouse
GEMINI_API_KEY=your_gemini_api_key
```

Use the actual environment variable names expected by the application code. Never commit your `.env` file or expose API keys and passwords.

### 5. Configure the MySQL database

Create the `genai_data_warehouse` database in MySQL and prepare the required warehouse tables using the project's database setup workflow.

### 6. Run the dashboard

```bash
streamlit run Main_Dashboard.py
```

## Dataset

The project uses the Superstore sales dataset, containing order details, customers, products, sales, discounts, and profit information.

## Future Enhancements

- Add more advanced business KPIs.
- Improve automated ETL workflows.
- Expand AI-powered recommendations.
- Deploy the dashboard to a cloud platform.

## Author

**Shakti Varshney**

GitHub: [Shakti-git07](https://github.com/Shakti-git07)

---

*Built as a data warehousing, analytics, and Generative AI project.*
