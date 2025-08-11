# Smart Accounts Management System

A comprehensive financial management application for self-employed individuals and accounting companies in the UK, built with Clean Architecture, Domain-Driven Design, and Hexagonal Architecture principles.

## 🚀 Quick Start

### Prerequisites
- Python 3.11.9+
- Node.js 18+
- PostgreSQL 14+
- Docker Desktop
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart-account
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   cd backend
   pip install -r requirements/dev.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run migrations
   python manage.py migrate
   
   # Start development server
   python manage.py runserver
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   
   # Set up environment variables
   cp .env.example .env.local
   # Edit .env.local with your configuration
   
   # Start development server
   npm run dev
   ```

4. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb smart_accounts_dev
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

## 📁 Project Structure

```
smart-account/
├── backend/                 # Django backend (Clean Architecture)
│   ├── domain/             # Business logic and entities
│   ├── application/        # Use cases and application services
│   ├── infrastructure/     # External services and data persistence
│   ├── interfaces/         # REST APIs and web interfaces
│   └── config/            # Django settings and configuration
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   └── public/            # Static assets
├── docs/                  # Project documentation
└── docker/               # Docker configuration
```

## 🏗️ Architecture

This project follows Clean Architecture principles with:

- **Domain Layer**: Pure business logic, entities, and value objects
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External services and data persistence
- **Interface Layer**: REST APIs and React frontend

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📡 API – Transactions

### Endpoints

- POST `/api/v1/transactions/` – Create a transaction
  - Body: `{ description, amount, currency?, type: income|expense, transaction_date (YYYY-MM-DD), receipt_id?, category? }`
  - Returns: `{ success, transaction_id }`

- GET `/api/v1/transactions/` – List with filters, sorting, pagination, and totals
  - Query params:
    - `dateFrom`, `dateTo`: YYYY-MM-DD
    - `type`: `income` or `expense` (comma-separated permitted)
    - `category`: category name(s), comma-separated
    - `sort`: `date` | `amount` | `category` (default `date`)
    - `order`: `asc` | `desc` (default `desc`)
    - `limit`: page size (default 50)
    - `offset`: page offset (default 0)
  - Response:
    - `items`: `{ id, description, merchant?, amount, currency, type, transaction_date, receipt_id?, category }[]`
    - `page`: `{ limit, offset, totalCount, hasNext, hasPrev }`
    - `totals`: `{ income: [{ currency, sum }], expense: [{ currency, sum }] }`

- GET `/api/v1/categories/` – List available transaction categories
  - Returns: `{ success, categories: string[] }`

- GET `/api/v1/transactions/summary/` – Totals-only with optional grouping
  - Query params: `dateFrom`, `dateTo`, optional `type`, `category`, `groupBy` (comma-separated: `month`, `category`)
  - Response: `{ success, totals: { income:[{currency,sum}], expense:[{currency,sum}] }, byMonth?, byCategory? }`

### Examples

List expenses in January 2024, 50 per page, sorted by amount ascending:

```
GET /api/v1/transactions/?type=expense&dateFrom=2024-01-01&dateTo=2024-01-31&sort=amount&order=asc&limit=50&offset=0
```

Next page:

```
GET /api/v1/transactions/?type=expense&dateFrom=2024-01-01&dateTo=2024-01-31&sort=amount&order=asc&limit=50&offset=50
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Architecture Plan](docs/Architecture_Plan.md)
- [Implementation Plan](docs/Implementation_Plan_Detailed.md)
- [Entity Relationship Design](docs/Entity_Relationship_Design.md)
- [UI/UX Design Document](docs/UI_UX_Design_Document.md)
- [RESTful API Documentation](docs/RESTful_API_Documentation.md)
- [Development Environment Setup](docs/Development_Environment_Setup.md)
- [Code Standards and Guidelines](docs/Code_Standards_and_Guidelines.md)
- [Testing Strategy and Procedures](docs/Testing_Strategy_and_Procedures.md)
- [Deployment Guide](docs/Deployment_Guide.md)

## 🚀 Features

- **Receipt Management**: OCR-powered receipt capture and data extraction
- **Expense Tracking**: Automated categorization and business/personal separation
- **Financial Reporting**: Real-time dashboards and export capabilities
- **Multi-tenant Architecture**: Support for individuals and accounting companies
- **Subscription Management**: Stripe integration with tiered pricing
- **UK Tax Compliance**: HMRC-compatible exports and VAT handling

## 🤝 Contributing

Please read our [Code Standards and Guidelines](docs/Code_Standards_and_Guidelines.md) before contributing.

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions, please refer to the documentation or create an issue in the repository. 