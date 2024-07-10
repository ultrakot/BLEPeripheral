import dbus

import argparse
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import time
import threading

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
BLUEZ_OBJECT_NAME = "/org/bluez"

GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response

    

# class Application(dbus.service.Object):
#     def __init__(self):
#         dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#         self.mainloop = GObject.MainLoop()
#         self.bus = BleTools.get_bus()
#         self.path = "/"
#         self.services = []
#         self.next_index = 0
#         dbus.service.Object.__init__(self, self.bus, self.path)

#     def get_path(self):
#         return dbus.ObjectPath(self.path)

#     def add_service(self, service):
#         self.services.append(service)

#     @dbus.service.method(DBUS_OM_IFACE, out_signature = "a{oa{sa{sv}}}")
#     def GetManagedObjects(self):
#         response = {}

#         for service in self.services:
#             response[service.get_path()] = service.get_properties()
#             chrcs = service.get_characteristics()
#             for chrc in chrcs:
#                 response[chrc.get_path()] = chrc.get_properties()
#                 descs = chrc.get_descriptors()
#                 for desc in descs:
#                     response[desc.get_path()] = desc.get_properties()

#         return response

#     def register_app_callback(self):
#         print("GATT application registered")

#     def register_app_error_callback(self, error):
#         print("Failed to register application: " + str(error))

#     def register(self):
#         adapter = BleTools.find_adapter(self.bus)

#         service_manager = dbus.Interface(
#                 self.bus.get_object(BLUEZ_SERVICE_NAME, adapter),
#                 GATT_MANAGER_IFACE)

#         service_manager.RegisterApplication(self.get_path(), {},
#                 reply_handler=self.register_app_callback,
#                 error_handler=self.register_app_error_callback)

#     def run(self):
#         self.mainloop.run()

#     def quit(self):
#         print("\nGATT application terminated")
#         self.mainloop.quit()
