export interface CloudProvider {
  id: string;
  name: string;
  hourlyRatePerNode: number;
  currency: string;
  logo: string;
  color: string;
  configFields: { id: string; label: string; placeholder: string }[];
}

export const CLOUD_PROVIDERS: CloudProvider[] = [
  {
    id: 'aws',
    name: 'Amazon Web Services',
    hourlyRatePerNode: 0.0464,
    currency: 'USD',
    logo: 'aws',
    color: '#ff9900',
    configFields: [
      { id: 'accessKey', label: 'AWS Access Key', placeholder: 'AKIA...' },
      { id: 'secretKey', label: 'AWS Secret Key', placeholder: 'wJalrXU...' },
      { id: 'region', label: 'Default Region', placeholder: 'us-east-1' }
    ]
  },
  {
    id: 'gcp',
    name: 'Google Cloud Platform',
    hourlyRatePerNode: 0.0475,
    currency: 'USD',
    logo: 'gcp',
    color: '#4285f4',
    configFields: [
      { id: 'projectId', label: 'Project ID', placeholder: 'my-project-123' },
      { id: 'keyFile', label: 'Service Account JSON', placeholder: '{ "type": "service_account", ... }' }
    ]
  },
  {
    id: 'azure',
    name: 'Microsoft Azure',
    hourlyRatePerNode: 0.05,
    currency: 'USD',
    logo: 'azure',
    color: '#0089d6',
    configFields: [
      { id: 'subscriptionId', label: 'Subscription ID', placeholder: '00000000-0000...' },
      { id: 'tenantId', label: 'Tenant ID', placeholder: '00000000-0000...' }
    ]
  }
];

export const calculateEstimatedCost = (providerId: string, nodeCount: number, durationHours: number = 1) => {
  const provider = CLOUD_PROVIDERS.find(p => p.id === providerId);
  if (!provider) return 0;
  return provider.hourlyRatePerNode * nodeCount * durationHours;
};
