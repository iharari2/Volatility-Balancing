# Volatility Balancing Frontend

A modern React-based frontend for the Volatility Balancing Trading System. This application provides an intuitive interface for managing positions, monitoring volatility triggers, and executing trades.

## Features

- **Dashboard**: Overview of all positions and system status
- **Position Management**: Create, monitor, and manage trading positions
- **Trading Interface**: Real-time price evaluation and order execution
- **Analytics**: Performance metrics and trading insights
- **Event Timeline**: Complete audit trail of all trading activities

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Query** for API state management
- **Recharts** for data visualization
- **React Router** for navigation

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## API Integration

The frontend communicates with the backend API through the following endpoints:

- `GET /api/positions` - List all positions
- `POST /api/positions` - Create a new position
- `GET /api/positions/:id` - Get position details
- `POST /api/positions/:id/anchor` - Set anchor price
- `POST /api/positions/:id/evaluate` - Evaluate price triggers
- `POST /api/positions/:id/orders` - Submit orders
- `POST /api/orders/:id/fill` - Fill orders
- `GET /api/positions/:id/events` - Get position events

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main layout wrapper
│   ├── PositionCard.tsx # Position display card
│   ├── TradingInterface.tsx # Trading controls
│   └── EventTimeline.tsx # Event history display
├── hooks/              # Custom React hooks
│   ├── usePositions.ts # Position-related API calls
│   └── useOrders.ts    # Order-related API calls
├── lib/                # Utility libraries
│   └── api.ts          # API client
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Positions.tsx   # Position management
│   ├── PositionDetail.tsx # Individual position view
│   ├── Trading.tsx     # Trading interface
│   └── Analytics.tsx   # Analytics and metrics
├── types/              # TypeScript type definitions
│   └── index.ts        # API and UI types
└── main.tsx           # Application entry point
```

## Key Features

### Position Management

- Create new positions with initial cash and shares
- Set anchor prices for volatility tracking
- Monitor position values and asset allocation

### Trading Interface

- Real-time price evaluation
- Automatic trigger detection (±3% thresholds)
- Manual and auto-sized order execution
- Order validation and guardrails

### Analytics Dashboard

- Position performance metrics
- Event distribution charts
- Trading activity insights
- Historical data visualization

### Event Tracking

- Complete audit trail of all actions
- Detailed event information with inputs/outputs
- Timeline view of position history

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

The project uses:

- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Tailwind CSS for styling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Volatility Balancing Trading System.
