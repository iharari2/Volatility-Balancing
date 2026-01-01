import React from 'react';
import { Info, Code, Database, BarChart3, Settings, Shield } from 'lucide-react';

const About: React.FC = () => {
  const features = [
    {
      icon: BarChart3,
      title: 'Advanced Analytics',
      description:
        'Comprehensive portfolio analysis with real-time performance metrics and risk assessment.',
    },
    {
      icon: Settings,
      title: 'Automated Trading',
      description:
        'Intelligent volatility-based rebalancing with customizable thresholds and risk parameters.',
    },
    {
      icon: Database,
      title: 'Data Management',
      description:
        'Secure storage and management of portfolio data with full audit trails and compliance.',
    },
    {
      icon: Shield,
      title: 'Risk Management',
      description:
        'Built-in risk controls and position sizing to protect your capital and optimize returns.',
    },
  ];

  const systemInfo = [
    { label: 'Version', value: '1.0.0' },
    { label: 'Build Date', value: '2024-01-15' },
    { label: 'Python Version', value: '3.11+' },
    { label: 'Node.js Version', value: '18.0+' },
    { label: 'Database', value: 'SQLite' },
    { label: 'API Framework', value: 'FastAPI' },
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">About Volatility Balancing</h1>
        <p className="text-gray-600">Advanced portfolio management and automated trading system</p>
      </div>

      {/* Overview Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <Info className="h-8 w-8 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">System Overview</h2>
            <p className="text-gray-600 mb-4">
              Volatility Balancing is a sophisticated portfolio management system designed to
              optimize returns through intelligent volatility-based rebalancing. The system
              automatically adjusts position sizes based on market volatility, helping to maximize
              returns while managing risk.
            </p>
            <p className="text-gray-600">
              Built with modern web technologies and advanced financial algorithms, it provides
              institutional-grade portfolio management capabilities in an intuitive, user-friendly
              interface.
            </p>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {features.map((feature, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <feature.icon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {systemInfo.map((info, index) => (
            <div key={index} className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm font-medium text-gray-500">{info.label}</span>
              <span className="text-sm text-gray-900">{info.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture Overview */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Architecture</h2>
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-700">
              <strong>Frontend:</strong> React with TypeScript, Tailwind CSS for responsive design
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">
              <strong>Backend:</strong> FastAPI with Python for high-performance API services
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-sm text-gray-700">
              <strong>Database:</strong> SQLite for development, PostgreSQL for production
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
            <span className="text-sm text-gray-700">
              <strong>Data Sources:</strong> Real-time market data integration with multiple
              providers
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-sm text-gray-700">
              <strong>Security:</strong> JWT authentication, encrypted data storage, audit logging
            </span>
          </div>
        </div>
      </div>

      {/* Key Capabilities */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Portfolio Management</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Real-time position tracking and monitoring</li>
              <li>• Automated rebalancing based on volatility thresholds</li>
              <li>• Risk management and position sizing controls</li>
              <li>• Performance attribution and analysis</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Trading & Execution</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Automated trade execution with configurable parameters</li>
              <li>• Manual intervention and override capabilities</li>
              <li>• Trade logging and audit trails</li>
              <li>• Commission and cost tracking</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Analysis & Reporting</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Comprehensive performance analytics</li>
              <li>• Risk metrics and volatility analysis</li>
              <li>• Excel export for further analysis</li>
              <li>• Interactive charts and visualizations</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Simulation & Optimization</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Historical backtesting capabilities</li>
              <li>• Parameter optimization and tuning</li>
              <li>• Scenario analysis and stress testing</li>
              <li>• Virtual portfolio management</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Contact & Support */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact & Support</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Technical Support</h3>
            <p className="text-sm text-gray-600 mb-2">
              For technical issues, feature requests, or system questions:
            </p>
            <p className="text-sm text-blue-600">support@volatilitybalancing.com</p>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Documentation</h3>
            <p className="text-sm text-gray-600 mb-2">Complete documentation and user guides:</p>
            <p className="text-sm text-blue-600">docs.volatilitybalancing.com</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
