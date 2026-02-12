// =========================
// frontend/src/components/ExcelExport.tsx
// =========================

import React, { useState } from 'react';
import { Download, FileSpreadsheet, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface ExcelExportProps {
  configId?: string;
  simulationId?: string;
  positionId?: string;
  dataType: 'optimization' | 'simulation' | 'trading' | 'position';
  title?: string;
  className?: string;
}

interface ExportFormat {
  name: string;
  value: string;
  description: string;
  mimeType: string;
}

interface ExportTemplate {
  name: string;
  description: string;
  sheets: string[];
  endpoint: string;
}

const ExcelExport: React.FC<ExcelExportProps> = ({
  configId,
  simulationId,
  positionId,
  dataType,
  title = 'Export to Excel',
  className = '',
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormats, setExportFormats] = useState<ExportFormat[]>([]);
  const [exportTemplates, setExportTemplates] = useState<ExportTemplate[]>([]);
  const [showFormats, setShowFormats] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleExport = async (format: string = 'xlsx') => {
    setIsExporting(true);

    try {
      let url = '';
      let filename = '';

      switch (dataType) {
        case 'optimization':
          if (!configId) throw new Error('Config ID is required for optimization export');
          url = `${API_BASE_URL}/v1/excel/optimization/${configId}/export?format=${format}`;
          filename = `optimization_results_${configId}_${new Date()
            .toISOString()
            .slice(0, 19)
            .replace(/:/g, '-')}.xlsx`;
          break;

        case 'simulation':
          if (!simulationId) throw new Error('Simulation ID is required for simulation export');
          url = `${API_BASE_URL}/v1/excel/simulation/${simulationId}/export?format=${format}`;
          filename = `simulation_results_${simulationId}_${new Date()
            .toISOString()
            .slice(0, 19)
            .replace(/:/g, '-')}.xlsx`;
          break;

        case 'trading':
          url = `${API_BASE_URL}/v1/excel/trading/export?format=${format}`;
          filename = `trading_data_${new Date()
            .toISOString()
            .slice(0, 19)
            .replace(/:/g, '-')}.xlsx`;
          break;

        case 'position':
          if (!positionId) throw new Error('Position ID is required for position export');
          url = `${API_BASE_URL}/v1/excel/positions/${positionId}/export?format=${format}`;
          filename = `position_data_${positionId}_${new Date()
            .toISOString()
            .slice(0, 19)
            .replace(/:/g, '-')}.xlsx`;
          break;

        default:
          throw new Error('Invalid data type');
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Get the filename from the Content-Disposition header if available
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Export failed:', error);
      toast.error(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const loadExportFormats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/excel/export/formats`);
      if (response.ok) {
        const data = await response.json();
        setExportFormats(data.formats || []);
      }
    } catch (error) {
      console.error('Failed to load export formats:', error);
    }
  };

  const loadExportTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/excel/export/templates`);
      if (response.ok) {
        const data = await response.json();
        setExportTemplates(data.templates || []);
      }
    } catch (error) {
      console.error('Failed to load export templates:', error);
    }
  };

  const handleShowFormats = () => {
    if (exportFormats.length === 0) {
      loadExportFormats();
    }
    setShowFormats(!showFormats);
  };

  const getTemplateForDataType = () => {
    return exportTemplates.find(
      (template) =>
        template.endpoint.includes(dataType) ||
        (dataType === 'optimization' && template.name.includes('Optimization')) ||
        (dataType === 'simulation' && template.name.includes('Simulation')) ||
        (dataType === 'trading' && template.name.includes('Trading')) ||
        (dataType === 'position' && template.name.includes('Position')),
    );
  };

  return (
    <div className={`excel-export ${className}`}>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => handleExport('xlsx')}
          disabled={isExporting}
          className={`
            inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md
            text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-200
          `}
        >
          {isExporting ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <FileSpreadsheet className="w-4 h-4 mr-2" />
          )}
          {isExporting ? 'Exporting...' : title}
        </button>

        <button
          onClick={handleShowFormats}
          className="
            inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md
            text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            transition-colors duration-200
          "
        >
          <Download className="w-4 h-4 mr-1" />
          Options
        </button>
      </div>

      {showFormats && (
        <div className="mt-2 p-4 bg-gray-50 rounded-md border">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Export Options</h4>

          {exportFormats.length > 0 && (
            <div className="mb-3">
              <label className="block text-xs font-medium text-gray-700 mb-1">Format:</label>
              <div className="space-y-1">
                {exportFormats.map((format) => (
                  <button
                    key={format.value}
                    onClick={() => handleExport(format.value)}
                    disabled={isExporting}
                    className="
                      block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded
                      disabled:opacity-50 disabled:cursor-not-allowed
                    "
                  >
                    <div className="font-medium">{format.name}</div>
                    <div className="text-xs text-gray-500">{format.description}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="text-xs text-gray-600">
            <div className="font-medium mb-1">Template includes:</div>
            <ul className="list-disc list-inside space-y-1">
              {getTemplateForDataType()?.sheets.map((sheet, index) => (
                <li key={index}>{sheet}</li>
              )) || ['Summary', 'Detailed Data', 'Analysis']}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExcelExport;
