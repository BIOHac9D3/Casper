output "vm_id" {
  description = "ID of the created VM"
  value       = azurerm_linux_virtual_machine.casper_vm.id
}

output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.casper_pip.ip_address
}

output "vm_name" {
  description = "Name of the created VM"
  value       = azurerm_linux_virtual_machine.casper_vm.name
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.casper_rg.name
}
