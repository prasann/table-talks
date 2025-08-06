# 📚 TableTalk Usage Guide

TableTalk is a natural language interface for exploring data schemas. Chat with your CSV and Parquet files using plain English!

## 🏪 Included Multi-Tenant Retail Dataset

TableTalk comes with a comprehensive multi-tenant retail dataset perfect for testing schema comparison and analysis features:

### 📁 Dataset Structure
- **15 CSV files** across **3 tenants** (US, EU, Asia)
- **5 tables per tenant**: customers, orders, products, reviews, payments
- **40-50 columns per table** with realistic retail data
- **Intentional schema noise** for testing:
  - **Naming variations**: `customer_id` vs `customerId` vs `cust_id`
  - **File naming patterns**: `customers_us.csv` vs `eu_customers.csv` vs `customersAsia.csv`
  - **Column order differences** across tenants
  - **Type inconsistencies** and **format variations**

### 🎯 Perfect for Testing
This dataset is specifically designed to showcase TableTalk's capabilities:
- **Schema difference analysis** across tenants
- **Semantic column matching** despite naming variations
- **Data quality issue detection** in multi-tenant environments
- **Cross-tenant relationship discovery**
- **Naming pattern inconsistency identification**

Files are located in `data/multi-tenant/` and automatically included with your TableTalk installation.

## 🚀 Quick Start

### 1. Setup & Start
```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama and models
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
./scripts/setup_phi4_function_calling.sh

# Start TableTalk
python tabletalk.py
```

### 2. Basic Commands
- `scan` - Analyze data files
- `status` - Show system status
- `help` - List commands  
- `quit` - Exit

## 💬 How to Use

### Natural Language Queries
Just type what you want to know!

**File Information:**
- "What files do we have?"
- "Show me the customers schema"
- "List columns in orders.csv"

**Data Quality:**
- "Find data quality issues"
- "Check for type mismatches"
- "Find naming inconsistencies"

**Semantic Search:**
- "Find user identifiers" (finds user_id, customer_id)
- "Show me timestamp columns" (finds date fields)
- "Customer related fields semantically"

**Schema Analysis:**
- "What columns are shared between files?"
- "Compare schemas between orders and customers"

**Schema Differences:**
- "Find schema differences between all files"
- "Analyze differences between schemas with semantic analysis"
- "Show me schema differences" (finds unique columns, type mismatches, semantic equivalents)

## 🧪 Testing Prompts

Here are specific prompts you can use to test different functionality with the included multi-tenant retail dataset:

### Basic Schema Operations
```bash
"List all files"
"Show me the schema for customers_us"
"What columns are in eu_orders.csv?"
"Get file statistics for multi-tenant data"
"Show me the structure of paymentsAsia.csv"
```

### Multi-Tenant Schema Analysis
```bash
# Compare schemas across tenants
"Find schema differences between customers_us and eu_customers"
"Compare order schemas across all tenants"
"Analyze differences between US and Asia payment schemas"

# Cross-tenant relationships
"Find common columns across all customer files"
"What payment columns appear in all regions?"
"Compare product schemas between tenants with semantic analysis"
```

### Schema Differences (Perfect for Multi-Tenant Testing!)
```bash
# Comprehensive multi-tenant analysis
"Find schema differences between all files"
"Analyze differences between schemas with semantic analysis"
"Compare schemas across tenants for customers tables"

# Specific tenant comparisons
"Find differences between customers_us and customersAsia"
"Compare eu_orders and ordersAsia schemas"
"Analyze payment schema differences across regions"
```

### Data Quality & Naming Inconsistencies
```bash
# Perfect for our noisy multi-tenant data!
"Detect data type inconsistencies across tenants"
"Find naming pattern issues in customer files"
"Check for semantic naming problems across regions"
"Find column naming variations between tenants"
"Identify abbreviation inconsistencies in schemas"
```

### Semantic Search with Retail Data
```bash
# Customer identification
"Find customer identifiers semantically"
"Show me user ID columns across all files"
"Find customer-related fields semantically"

# Temporal data
"Show me timestamp columns"
"Find date-related fields across tenants"
"Search for order date variations"

# Financial data
"Search for price related columns"
"Find payment amount fields semantically"
"Show me currency-related columns"

# Product information
"Find product identifier columns"
"Search for inventory-related fields"
"Show me product description columns"
```

### Advanced Multi-Tenant Analysis
```bash
"Run concept evolution analysis across tenants"
"Check concept consistency between regions"
"Find potential missing columns in Asian schemas"
"Analyze schema similarity between EU and US with threshold 0.8"
"Group payment columns by semantic concepts across tenants"
```

## 🧠 Semantic Search

TableTalk includes AI-powered semantic search that understands the **meaning** behind your queries.

### Automatic Activation
Use phrases like "semantically", "semantic search", "find similar", "related columns" to enable semantic search automatically.

### Examples
```bash
# Traditional: exact matches only
search customer → finds only "customer_id"

# Semantic: concept understanding  
find user identifiers semantically → finds "user_id", "customer_id", "review_id"
show me timestamp columns → finds "created_date", "order_date", "signup_date"
```

### Installation
For semantic search capabilities:
```bash
pip install sentence-transformers scikit-learn
```

## �📊 Example Session

```
## 📊 Example Session

```
📊 TableTalk - Your Data Schema Explorer

> scan
🔍 Scanning data files...
✅ Found 15 multi-tenant files: customers_us.csv, eu_customers.csv, customersAsia.csv, 
   orders_us.csv, eu_orders.csv, ordersAsia.csv, products_us.csv, eu_products.csv, 
   productsAsia.csv, reviews_us.csv, eu_reviews.csv, reviewsAsia.csv, 
   payments_us.csv, eu_payments.csv, paymentsAsia.csv

> What files do we have?
📁 **Multi-Tenant Retail Dataset:**
• **US Region (5 files):** customers_us.csv, orders_us.csv, products_us.csv, reviews_us.csv, payments_us.csv
• **EU Region (5 files):** eu_customers.csv, eu_orders.csv, eu_products.csv, eu_reviews.csv, eu_payments.csv  
• **Asia Region (5 files):** customersAsia.csv, ordersAsia.csv, productsAsia.csv, reviewsAsia.csv, paymentsAsia.csv

> Show me the schema for customers_us
📋 **customers_us.csv Schema:**
• customer_id (integer) - Customer identifier
• first_name (string) - Customer first name
• last_name (string) - Customer last name
• email (string) - Customer email address
• phone (string) - Phone number
• address (string) - Customer address
• signup_date (string) - Registration date
• loyalty_points (integer) - Loyalty program points
• preferred_language (string) - Language preference
• marketing_opt_in (boolean) - Marketing consent
... and 34 more columns

> Find schema differences between customers_us and eu_customers
**Schema Difference Analysis:**

**customers_us.csv** vs **eu_customers.csv**
  Overall similarity: 0.891

  Column naming differences:
    • customer_id vs customerId
    • first_name vs firstName
    • last_name vs lastName
    • email vs emailAddress
    • phone vs phoneNumber
    • address vs streetAddress
    • signup_date vs registrationDate
    • loyalty_points vs points
    • preferred_language vs language
    • marketing_opt_in vs marketingConsent

  Semantic equivalents (10):
    • customer_id ↔ customerId (similarity: 0.95)
    • first_name ↔ firstName (similarity: 0.98)
    • email ↔ emailAddress (similarity: 0.89)
    • phone ↔ phoneNumber (similarity: 0.92)
    • address ↔ streetAddress (similarity: 0.87)

> Find customer identifiers semantically
📍 **Customer Identifier Fields Found:**
• customers_us.csv → customer_id (similarity: 1.00)
• eu_customers.csv → customerId (similarity: 0.95)
• customersAsia.csv → cust_id (similarity: 0.91)
• orders_us.csv → customer_id (similarity: 1.00)
• eu_orders.csv → customerId (similarity: 0.95)
• ordersAsia.csv → cust_id (similarity: 0.91)
• reviews_us.csv → customer_id (similarity: 1.00)
• eu_reviews.csv → customerId (similarity: 0.95)
• reviewsAsia.csv → cust_id (similarity: 0.91)

> Check for naming pattern issues across tenants
🔍 **Multi-Tenant Naming Analysis:**
⚠️ **Inconsistent Naming Patterns:**
• Customer ID: customer_id (US) vs customerId (EU) vs cust_id (Asia)
• Order ID: order_id (US) vs orderId (EU) vs orderID (Asia)
• Product ID: product_id (US) vs productId (EU) vs prod_id (Asia)
• Date fields: order_date (US) vs orderDate (EU) vs orderDt (Asia)
• Address: address (US) vs streetAddress (EU) vs address (Asia)

⚠️ **Type Mismatches:**
• customer_id: integer (US) vs string (EU) vs integer (Asia)
• price: float (US) vs decimal (EU) vs float (Asia)

> Find schema differences with semantic analysis across all files
**Multi-Tenant Schema Analysis** (Top differences)

**Customers Tables Comparison:**
  US ↔ EU similarity: 0.891 (10 naming differences, same structure)
  US ↔ Asia similarity: 0.856 (15 naming differences, column order varies)
  EU ↔ Asia similarity: 0.823 (20 naming differences, mixed conventions)

**Orders Tables Comparison:**
  US ↔ EU similarity: 0.867 (8 naming differences)
  US ↔ Asia similarity: 0.798 (12 naming differences, abbreviated columns)
  EU ↔ Asia similarity: 0.745 (18 naming differences, format inconsistencies)

**Key Findings:**
• US uses snake_case (customer_id, order_date)
• EU uses camelCase (customerId, orderDate)  
• Asia uses mixed/abbreviated (cust_id, orderDt)
• All regions have same logical structure but different naming
• Semantic equivalents found across 95% of columns
```
```

## 🎯 What TableTalk Can Do

### 📁 File Operations
- **Scan files**: Discover CSV/Parquet files automatically
- **Show schemas**: Column names, types, and statistics
- **File comparison**: Find similarities and differences

### 🔍 Data Quality
- **Type checking**: Find inconsistent data types across files
- **Column analysis**: Detect naming variations and patterns
- **Schema validation**: Identify potential data issues

### 🧠 Semantic Intelligence
- **Concept search**: Find "user identifiers" across all files
- **Pattern detection**: Group similar columns semantically
- **Smart suggestions**: AI-powered analysis recommendations

### 🔄 Schema Differences Analysis
- **Comprehensive comparison**: Compare schemas across all file pairs
- **Unique columns**: Identify columns that exist only in specific files
- **Type mismatches**: Find common columns with different data types
- **Semantic equivalents**: Detect columns with different names but similar meanings
- **Missing column analysis**: Suggest potentially missing columns based on semantic similarity

**Example Schema Difference Analysis:**
```
> find schema differences with semantic analysis

customers.csv vs orders.csv (similarity: 0.091)
  Columns only in customers.csv (5):
    • last_name (string)
    • email (string)
    • first_name (string)
    • signup_date (string)
    • is_active (boolean)

  Columns only in orders.csv (5):
    • quantity (integer)
    • price (float)
    • product_name (string)
    • order_date (string)
    • order_id (integer)

  Semantic equivalents (1):
    • customer_id ↔ user_id (similarity: 0.85)

  Type mismatches (1):
    • customer_id: integer vs string
```

## � Testing Tips & Best Practices

### For Schema Differences Analysis
- **Use semantic analysis** for better results: Add "semantic" or "semantically" to your query
- **Adjust thresholds**: Try different values like `"threshold 0.7"` for more/fewer matches
- **Test with diverse data**: Schema differences work best with files that have some overlap
- **Check type mismatches**: Look for columns with same names but different data types

### Effective Query Patterns
**✅ Good queries:**
- `"find schema differences with semantic analysis"`
- `"analyze differences between schemas semantically"`
- `"find relationships with analysis type schema_differences"`

**❌ Avoid:**
- Overly complex queries with multiple requirements
- Queries without semantic keywords when you want semantic analysis
- Very low thresholds (< 0.5) which may produce too many false positives

### Performance Tips
- **First semantic query** takes longer (~5 seconds) as AI models load
- **Subsequent queries** are much faster (< 1 second)
- **Large datasets**: Consider testing with smaller sample files first
- **Threshold tuning**: Start with 0.7, adjust based on results

### Expected Results
When testing schema differences, expect to see:
- **Similarity scores** between 0.0 and 1.0
- **Unique columns** listed per file with data types
- **Type mismatches** for columns with same names but different types
- **Semantic equivalents** when semantic analysis is enabled
- **Missing column suggestions** based on semantic similarity

## �🚨 Troubleshooting

### Common Issues
**"No LLM available":**
```bash
ollama serve
./scripts/setup_phi4_function_calling.sh
```

**"No data files found":**
- Put CSV/Parquet files in the `data/` folder
- Run `scan` command

**Slow responses:**
- First semantic query loads AI models (~5 seconds)
- Subsequent queries are fast (<1 second)

### Getting Help
- Type `help` for commands
- Type `status` to check system
- Check `logs/tabletalk.log` for errors

## 🚀 Quick Reference

### Essential Commands
| Category | Command | Example |
|----------|---------|---------|
| **Files** | List files | `"What files do we have?"` |
| **Schemas** | Show schema | `"Show me the customers schema"` |
| **Differences** | Schema diff | `"find schema differences with semantic analysis"` |
| **Quality** | Type issues | `"Check for type mismatches"` |
| **Semantic** | Find concepts | `"Find user identifiers semantically"` |
| **Analysis** | Relationships | `"What columns are shared between files?"` |

### Tool Parameters (Advanced)
- **analysis_type**: `"common_columns"`, `"similar_schemas"`, `"semantic_groups"`, `"concept_evolution"`, `"schema_differences"`
- **semantic**: Add `"semantic"` or `"semantically"` to enable
- **threshold**: Specify like `"threshold 0.7"` (0.5-0.9 range)

### Sample Data for Testing
TableTalk includes a comprehensive multi-tenant retail dataset in `data/multi-tenant/` with 15 CSV files across 3 regions. 

**If you want to create additional test data**, here are some examples:
```bash
# simple_customers.csv
customer_id,first_name,last_name,email,signup_date,is_active
1,John,Doe,john@email.com,2023-01-01,true

# simple_orders.csv  
order_id,customer_id,product_name,price,quantity,order_date
1,1,Widget,29.99,2,2023-01-15
```

**But we recommend starting with the included multi-tenant dataset** which provides rich, realistic scenarios for testing schema differences, semantic matching, and data quality analysis!
