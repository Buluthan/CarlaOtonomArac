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

# Main
if __name__ == "__main__":
    client = connect_to_carla()
    if client:
        world = client.get_world()

        # Tüm katmanları yükle ve göster
        load_and_show_all_layers(world)
    else:
        print("CARLA'ya bağlanılamadı.")