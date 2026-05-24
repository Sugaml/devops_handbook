@description('Region for resources')
param location string = resourceGroup().location

@description('Base name for storage account (must be unique globally)')
param storageAccountName string

@description('Tags applied to all resources')
param tags object = {
  Project: 'devops-handbook'
  Day: '5'
}

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: tags
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'artifacts'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountId string = storage.id
output blobEndpoint string = storage.properties.primaryEndpoints.blob
