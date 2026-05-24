@description('Azure region')
param location string = resourceGroup().location

@description('Environment name')
@allowed(['lab', 'dev', 'prod'])
param environment string = 'lab'

@description('Admin SSH public key')
param adminPublicKey string

@description('Unique suffix for globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

var vmName = 'vm-handbook-${environment}'
var storageName = 'st${uniqueSuffix}'
var kvName = 'kv-${uniqueSuffix}'

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: 'vnet-handbook-${environment}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.40.0.0/16']
    }
    subnets: [
      {
        name: 'subnet-web'
        properties: {
          addressPrefix: '10.40.1.0/24'
        }
      }
    ]
  }
  tags: {
    Project: 'devops-handbook'
    Environment: environment
  }
}

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: 'nsg-web-${environment}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-SSH'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '22'
        }
      }
      {
        name: 'Allow-HTTP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          destinationPortRange: '80'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource pip 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: 'pip-${vmName}'
  location: location
  sku: { name: 'Standard' }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: 'nic-${vmName}'
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: { id: vnet.properties.subnets[0].id }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: { id: pip.id }
        }
      }
    ]
    networkSecurityGroup: { id: nsg.id }
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2023-09-01' = {
  name: vmName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_B1s'
    }
    osProfile: {
      computerName: vmName
      adminUsername: 'azureuser'
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/azureuser/.ssh/authorized_keys'
              keyData: adminPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'StandardSSD_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        { id: nic.id }
      ]
    }
  }
  tags: {
    Project: 'devops-handbook'
    Environment: environment
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableRbacAuthorization: true
    enabledForTemplateDeployment: true
  }
}

resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(kv.id, vm.id, 'Secrets User')
  scope: kv
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: vm.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output vmPublicIp string = pip.properties.ipAddress
output storageAccountName string = storage.name
output keyVaultUri string = kv.properties.vaultUri
output vmPrincipalId string = vm.identity.principalId
