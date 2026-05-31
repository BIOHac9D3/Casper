terraform {
  required_version = ">= 1.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "casper_rg" {
  name     = "casper-${var.environment}-rg"
  location = var.location
}

resource "azurerm_virtual_network" "casper_vnet" {
  name                = "casper-${var.environment}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.casper_rg.location
  resource_group_name = azurerm_resource_group.casper_rg.name
}

resource "azurerm_subnet" "casper_subnet" {
  name                 = "casper-${var.environment}-subnet"
  resource_group_name  = azurerm_resource_group.casper_rg.name
  virtual_network_name = azurerm_virtual_network.casper_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "casper_pip" {
  name                = "casper-${var.environment}-pip"
  location            = azurerm_resource_group.casper_rg.location
  resource_group_name = azurerm_resource_group.casper_rg.name
  allocation_method   = "Dynamic"
}

resource "azurerm_network_interface" "casper_nic" {
  name                = "casper-${var.environment}-nic"
  location            = azurerm_resource_group.casper_rg.location
  resource_group_name = azurerm_resource_group.casper_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.casper_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.casper_pip.id
  }
}

resource "azurerm_linux_virtual_machine" "casper_vm" {
  name                = "casper-${var.environment}-vm"
  location            = azurerm_resource_group.casper_rg.location
  resource_group_name = azurerm_resource_group.casper_rg.name
  size                = var.vm_size

  network_interface_ids = [
    azurerm_network_interface.casper_nic.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "20.04-LTS"
    version   = "latest"
  }

  computer_name                   = "casper-node"
  admin_username                  = var.admin_username
  disable_password_authentication = true

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  tags = {
    Environment = var.environment
    Project     = "Casper"
  }
}
