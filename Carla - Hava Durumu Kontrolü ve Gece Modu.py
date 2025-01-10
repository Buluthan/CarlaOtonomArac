import carla

# CARLA'ya Bağlan
def connect_to_carla():
    try:
        client = carla.Client('localhost', 2000)  # CARLA server adresi ve portu
        client.set_timeout(10.0)
        print("CARLA'ya başarıyla bağlanıldı!")
        return client
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

# Tüm Katmanları Yükleme ve Görünürlük Ayarları
def load_and_show_all_layers(world):
    try:
        # Mevcut katman etiketlerini al
        available_layers = [
            carla.CityObjectLabel.Buildings,
            carla.CityObjectLabel.Roads,
            carla.CityObjectLabel.Fences,
            carla.CityObjectLabel.Vegetation,
            carla.CityObjectLabel.Poles,
            carla.CityObjectLabel.Walls,
            carla.CityObjectLabel.All
        ]

        print("Harita katmanları yükleniyor...")
        for layer in available_layers:
            layer_objects = world.get_environment_objects(layer)
            print(f"{layer.name} katmanında {len(layer_objects)} nesne yüklendi.")

            # Tüm nesneleri görünür yap
            for obj in layer_objects:
                obj.set_enable_mesh(True)

        print("Tüm katmanlar başarıyla yüklendi ve görünür hale getirildi.")
    except Exception as e:
        print(f"Katman yükleme hatası: {e}")

# Hava Durumu Ayarları
def set_weather(world, weather_type="clear"):
    try:
        weather = world.get_weather()

        if weather_type == "clear":
            weather.cloudiness = 0.0
            weather.precipitation = 0.0
            weather.fog_density = 0.0
        elif weather_type == "rainy":
            weather.cloudiness = 80.0
            weather.precipitation = 80.0
            weather.fog_density = 20.0
        elif weather_type == "foggy":
            weather.cloudiness = 50.0
            weather.precipitation = 0.0
            weather.fog_density = 80.0

        world.set_weather(weather)
        print(f"Hava durumu '{weather_type}' olarak ayarlandı.")
    except Exception as e:
        print(f"Hava durumu ayarlanırken hata oluştu: {e}")

# Gece Modu Ayarları
def set_night_mode(world, enable_night=True):
    try:
        if enable_night:
            world.set_weather(carla.WeatherParameters(sun_altitude_angle=-90.0))
            print("Gece modu etkinleştirildi.")
        else:
            world.set_weather(carla.WeatherParameters(sun_altitude_angle=90.0))
            print("Gündüz modu etkinleştirildi.")
    except Exception as e:
        print(f"Gece modu ayarlanırken hata oluştu: {e}")

# Main
if __name__ == "__main__":
    client = connect_to_carla()
    if client:
        world = client.get_world()

        # Tüm katmanları yükle ve göster
        load_and_show_all_layers(world)

        # Hava durumunu ayarla
        set_weather(world, weather_type="rainy")

        # Gece modunu etkinleştir
        set_night_mode(world, enable_night=True)
    else:
        print("CARLA'ya bağlanılamadı.")