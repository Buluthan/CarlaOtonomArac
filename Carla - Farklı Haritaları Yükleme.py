import carla
import random
import matplotlib.pyplot as plt
import numpy as np

# 1. Simülasyon Ortamı Kurulumu
def connect_to_carla():
    try:
        client = carla.Client('localhost', 2000)  # CARLA server’a bağlan
        client.set_timeout(2.0)
        world = client.get_world()
        return world
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

# 2. Araç Oluşturma ve Kontrol
def spawn_vehicle(world):
    try:
        blueprint_library = world.get_blueprint_library()
        vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))  # Rastgele bir araç seç
        spawn_point = random.choice(world.get_map().get_spawn_points())  # Rastgele bir başlangıç noktası seç
        vehicle = world.spawn_actor(vehicle_bp, spawn_point)
        return vehicle
    except Exception as e:
        print(f"Araç oluşturma hatası: {e}")
        return None

# 3. Çıkış için Simüle Edilmiş Veri
def generate_simulation_data():
    time = np.linspace(0, 10, 100)  # Zaman
    speed = 30 + 5 * np.sin(time)  # Hız verileri (örnek dalgalı bir hız)
    return time, speed

# 4. Grafik Oluşturma
def plot_simulation_results(time, speed):
    plt.figure(figsize=(10, 5))
    plt.plot(time, speed, label='Araç Hızı', color='blue')
    plt.title('Araç Hızı Simülasyonu')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Hız (km/saat)')
    plt.legend()
    plt.grid()
    plt.savefig('simulation_results.png')  # Sonucu kaydet
    plt.show()

# Main
if __name__ == "__main__":
    print("Simülasyon başlıyor...")
    world = connect_to_carla()
    if world:
        vehicle = spawn_vehicle(world)
        if vehicle:
            print("Araç başarıyla oluşturuldu!")
            time, speed = generate_simulation_data()
            plot_simulation_results(time, speed)
            print("Simülasyon tamamlandı. Çıktı 'simulation_results.png' olarak kaydedildi.")
        else:
            print("Araç oluşturulamadı.")
    else:
        print("Simülasyon ortamı oluşturulamadı.")