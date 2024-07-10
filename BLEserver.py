import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from optparse import OptionParser

import array
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
import sys

from ble_server.ble_core.Characteristic import Characteristic 
from ble_server.ble_core.Advertisement import Advertisement
from ble_server.ble_core.Service import Service
from ble_server.ble_core.Descriptor import Descriptor
from ble_server.ble_core.Application import Application
#from ble_core.Agent import Agent

from random import randint

BUS_NAME = 'org.bluez'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = "/test/agent"

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
NOTIFY_TIMEOUT = 5000

class TestAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_local_name("MyBouncer")
        self.include_tx_power = True


class TestService(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """
    TEST_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.TEST_SVC_UUID, True)        
        #self.add_characteristic(NotifyCharacteristic(bus, 0, self))
        self.add_characteristic(TestCharacteristic(bus, 1, self))
        self.add_characteristic(TheAnswerMachineChrc(bus, 0, self))
        self.add_characteristic(AutoNotifyCharacteristic(bus, 2, self))

class AutoNotifyCharacteristic(Characteristic):
    AUTO_NOTIFY_UUID = '7396d4c8-4882-4095-b0f0-4250a8df2e43'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.AUTO_NOTIFY_UUID,
                ['notify'],
                service)
        self.notifying = True  # Always notifying by default

    def update_value(self, value):
        if not self.notifying:
            return
        dbus_value = [dbus.Byte(value % 256)]
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': dbus_value}, [])
        print('Updated value: ' + repr(dbus_value))

class TheAnswerMachineChrc(Characteristic):
    TEST_CHRC_NOTIFY_UUID = '7396d4c8-4882-4095-b0f0-4250a8df2e40'
 
    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.TEST_CHRC_NOTIFY_UUID,
                ['notify'],
                service)
        self.notifying = False
        #self.counter = 0


    def tfu_notify_cb(self):
        value = []
        value.append(dbus.Byte(0x06))
        
        # if self.counter < 50:
        #     value[0] = dbus.Byte(0x08)
            
       # self.counter += 1
        
        print('Updating value: ' + repr(value))
        self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': value }, [])

        return self.notifying        

    def _update_simulation(self):
        print('Update notification vLUE 42')

        if not self.notifying:
            return

        GObject.idle_add(1000, self.tfu_notify_cb)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self.add_timeout(NOTIFY_TIMEOUT, self.trigger_properties_changed_callback(97))
        #self._update_simulation()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
        self._update_simulation()     
    
    def trigger_properties_changed_callback(self, flag):
        flag = []
        if self.notifying :
            self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': flag }, [])
            print('Triggered PropertiesChanged with flag: ' + repr(flag))
        return self.notifying 


class HeartRateMeasurementChrc(Characteristic):
    #HR_MSRMT_UUID = '00002a37-0000-1000-8000-00805f9b34fb'
    TEST_CHRC_NOTIFY_UUID = '7396d4c8-4882-4095-b0f0-4250a8df2e40'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.TEST_CHRC_NOTIFY_UUID,
                ['notify'],
                service)
        self.notifying = False
        self.hr_ee_count = 0

    def hr_msrmt_cb(self):
        value = []
        value.append(dbus.Byte(0x06))

        value.append(dbus.Byte(randint(90, 130)))

        if self.hr_ee_count % 10 == 0:
            value[0] = dbus.Byte(0x08)
            #value.append(dbus.Byte(self.service.energy_expended & 0xff))
            #alue.append(dbus.Byte((self.service.energy_expended >> 8) & 0xff))

        #self.service.energy_expended = \
        #        min(0xffff, self.service.energy_expended + 1)
        self.hr_ee_count += 1

        print('Updating value: ' + repr(value))

        self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': value }, [])

        return self.notifying

    def _update_hr_msrmt_simulation(self):
        print('Update HR Measurement Simulation')

        if not self.notifying:
            return

        GObject.timeout_add(1000, self.hr_msrmt_cb)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self._update_hr_msrmt_simulation()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
        self._update_hr_msrmt_simulation()
        

class NotifyCharacteristic(Characteristic):
    """

    """    
    TEST_CHRC_NOTIFY_UUID = '7396d4c8-4882-4095-b0f0-4250a8df2e40'
    NOTIFICATION_INTERVAL = 5000  # seconds

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self,
            bus,
            index,
            self.TEST_CHRC_NOTIFY_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.value = dbus.Byte(0x2A)
        self.notifying = False
        self.counter = 0

    def ReadValue(self, options):
        #Sprint('TestCharacteristic Read: ' + repr(self.value))
        return self.value

    def StartNotify(self):
        if not self.notifying:
           print('Notifications started in BLE server 1')
           #self.notifying = True
           self.counter = 0
           print('Updating value: ' + repr(value))
           self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': dbus.Byte(0x2A) }, [])
           print('hello')
           #GLib.timeout_add_seconds(self.NOTIFICATION_INTERVAL, self.notify_value)
           #print('GLib was sent')

    def StopNotify(self):
        if self.notifying:
            print('Notifications stopped')
            self.notifying = False

    def notify_value(self):
        if self.notifying:
           self.value = dbus.Byte(0x2A)
            
           print('Updating value: ' + repr(value))
            
            #self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': self.value }, [])

           self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': dbus.Byte(0x2A) }, [])

           self.counter += 1
           print(f'Notification {self.counter}: {self.value}')
            # Check if all notifications have been sent
           if self.counter >= 100:  
              self.StopNotify()
              return False  # Stop the timer
        return True  # Continue the timer if still notifying


class TestCharacteristic(Characteristic):
    """
    Dummy test characteristic. Allows writing arbitrary bytes to its value, and
    contains "extended properties", as well as a test descriptor.

    """
    TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef1'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self,
                bus, 
                index,
                self.TEST_CHRC_UUID,
                ['read', 'write', 'writable-auxiliaries'],
                service)
        self.value = []
        self.value.append(dbus.Byte(0x2A))
        self.add_descriptor(TestDescriptor(bus, 0, self))

    def ReadValue(self, options):
        print('TestCharacteristic Read: ' + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        print('TestCharacteristic Write: ' + repr(value))
        self.value = value


class TestDescriptor(Descriptor):
    """
    Dummy test descriptor. Returns a static value.

    """
    TEST_DESC_UUID = '12345678-1234-5678-1234-56789abcdef2'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
                self, 
                self.TEST_DESC_UUID,
                ['read', 'write'],
                characteristic)

    def ReadValue(self, options):
        return [
                dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
        ]


#general registering and adapter menagement code, main loop

def register_app_cb():
    print('GATT application registered')


def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def register_ad_callback(self):
    print("GATT advertisement registered")

def register_ad_error_callback(self):
    print("Failed to register GATT advertisement")




def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o

    return None

# def main():
#     global mainloop

#     dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#     bus = dbus.SystemBus()
#     adapter = find_adapter(bus)
#     if not adapter:
#         print('GattManager1 interface not found')
#         return
    
#     adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),"org.freedesktop.DBus.Properties")
#     adapter_props.Set("org.bluez.Adapter1", "Discoverable", True)

#     service_manager = dbus.Interface(
#             bus.get_object(BLUEZ_SERVICE_NAME, adapter),
#             GATT_MANAGER_IFACE)
    
#     ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
#             LE_ADVERTISING_MANAGER_IFACE)

#     app = Application(bus)
#     app.add_service(TestService(bus, 0))
#     #app.register()
#     adv = TestAdvertisement(bus, 0)
#     #adv.register()


#     mainloop = GObject.MainLoop()

#     # Register the Agent
#     capability = "NoInputNoOutput"
#     agent_path = "/test/agent"
#     agent = Agent(bus, agent_path)
#     agent_manager = dbus.Interface(bus.get_object(BUS_NAME, "/org/bluez"), "org.bluez.AgentManager1")
#     agent_manager.RegisterAgent(agent_path, capability)
#     agent_manager.RequestDefaultAgent(agent_path)
#     print("Agent registered")    
    
   

#     print('Registering GATT application...')

#     service_manager.RegisterApplication(app.get_path(), {},
#                                     reply_handler=register_app_cb,
#                                     error_handler=register_app_error_cb)
                                
#     ad_manager.RegisterAdvertisement(adv.get_path(), {},
#                                     reply_handler=adv.register_ad_callback,
#                                     error_handler=adv.register_ad_error_callback)

#     mainloop.run()

# if __name__ == '__main__':
#     main()
