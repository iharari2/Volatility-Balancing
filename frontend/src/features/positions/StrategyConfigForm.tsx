export default function StrategyConfigForm() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Configuration</h3>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Trigger Thresholds</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">Up Threshold %</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.03"
            />
            <p className="mt-1 text-sm text-gray-500">
              Sell trigger when price exceeds anchor by this %
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Down Threshold %</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.03"
            />
            <p className="mt-1 text-sm text-gray-500">
              Buy trigger when price falls below anchor by this %
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Guardrails</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">Min Stock %</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.25"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Max Stock %</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.75"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Max Trade % of Position
            </label>
            <input
              type="number"
              step="0.01"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.50"
            />
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Commission</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Commission Rate (bps or %)
            </label>
            <input
              type="text"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              defaultValue="0.10%"
              placeholder="0.10%"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Per-asset overrides:
          </label>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Asset
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Rate
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-4 py-2 text-sm text-gray-900">AAPL</td>
                  <td className="px-4 py-2 text-sm text-gray-900">0.10%</td>
                  <td className="px-4 py-2 text-sm">
                    <button className="text-red-600 hover:text-red-900">Remove</button>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-sm text-gray-900">MSFT</td>
                  <td className="px-4 py-2 text-sm text-gray-900">0.08%</td>
                  <td className="px-4 py-2 text-sm">
                    <button className="text-red-600 hover:text-red-900">Remove</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <button className="mt-2 text-sm text-primary-600 hover:text-primary-900 font-medium">
            + Add Override
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Market Hours</h4>
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Trade during:</p>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="market-hours"
                  value="market-only"
                  defaultChecked
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Market Hours Only</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="market-hours"
                  value="market-after-hours"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Market Hours + After Hours</span>
              </label>
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700">Market Status:</p>
            <p className="text-sm text-gray-500">OPEN</p>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button className="inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
          Reset to Default Template
        </button>
        <button className="inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-sm font-medium text-white hover:bg-primary-700">
          Save Config
        </button>
      </div>
    </div>
  );
}

















