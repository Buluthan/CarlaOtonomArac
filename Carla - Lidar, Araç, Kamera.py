import carla
import os
import datetime

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

# Araç Ekleme
def spawn_vehicle(world):
    try:
        blueprint_library = world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter("vehicle.dodge.charger_2020")[0]  # Dodge Charger 2020 aracı seç
        spawn_points = world.get_map().get_spawn_points()
        if spawn_points:
            spawn_point = spawn_points[0]  # İlk mevcut noktada aracı spawn et
            vehicle = world.spawn_actor(vehicle_bp, spawn_point)
            print("Dodge Charger 2020 başarıyla spawn edildi.")
            return vehicle
        else:
            print("Spawn noktası bulunamadı.")
            return None
    except Exception as e:
        print(f"Araç eklenirken hata oluştu: {e}")
        return None

# Araç Kontrolü
def control_vehicle(vehicle):
    try:
        if vehicle:
            control = carla.VehicleControl()
            control.throttle = 0.5  # Gaz verme
            control.steer = 0.0  # Düz sürüş
            vehicle.apply_control(control)
            print("Araç hareket etmeye başladı.")
        else:
            print("Araç mevcut değil, kontrol edilemiyor.")
    except Exception as e:
        print(f"Araç kontrol edilirken hata oluştu: {e}")

# Şerit Değiştirme
def change_lane(vehicle, direction):
    try:
        if vehicle:
            control = carla.VehicleControl()
            control.throttle = 0.5  # Gaz verme
            if direction == "left":
                control.steer = -0.3  # Sola dönüş için direksiyon açısı
                print("Araç sola şerit değiştiriyor.")
            elif direction == "right":
                control.steer = 0.3  # Sağa dönüş için direksiyon açısı
                print("Araç sağa şerit değiştiriyor.")
            else:
                control.steer = 0.0  # Düz sürüş
                print("Şerit değiştirme yönü belirtilmedi, araç düz gidiyor.")

            vehicle.apply_control(control)
        else:
            print("Araç mevcut değil, şerit değiştirilemiyor.")
    except Exception as e:
        print(f"Şerit değiştirirken hata oluştu: {e}")

# Lane Invasion Sensörü Ekleme
def attach_lane_invasion_sensor(vehicle, world):
    try:
        blueprint_library = world.get_blueprint_library()
        lane_invasion_bp = blueprint_library.find('sensor.other.lane_invasion')

        # Şerit ihlali sensörü araca bağlanır
        lane_invasion_transform = carla.Transform(carla.Location(x=0.0, z=2.0))
        lane_invasion_sensor = world.spawn_actor(lane_invasion_bp, lane_invasion_transform, attach_to=vehicle)
        print("Şerit ihlali sensörü başarıyla araca bağlandı.")

        def handle_lane_invasion(event):
            print("Şerit ihlali algılandı! İhlal edilen yol çizgileri:")
            for marking in event.crossed_lane_markings:
                print(f"- {marking.type.name}")

        lane_invasion_sensor.listen(lambda event: handle_lane_invasion(event))

        return lane_invasion_sensor
    except Exception as e:
        print(f"Şerit ihlali sensörü bağlanırken hata oluştu: {e}")
        return None

# Kamera Ekleyip Fotoğraf Çekme
def attach_camera_and_capture(vehicle, world):
    try:
        blueprint_library = world.get_blueprint_library()
        camera_bp = blueprint_library.find('sensor.camera.rgb')

        # Kamera ayarları
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        camera_bp.set_attribute('fov', '90')

        # Kamera araca bağlanır
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # Araç üzerinde konumlandırma
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        print("Kamera başarıyla araca bağlandı.")

        # Fotoğraf kaydetme
        output_dir = "output_images"
        os.makedirs(output_dir, exist_ok=True)

        def save_image(image):
            image.convert(carla.ColorConverter.Raw)
            filename = os.path.join(output_dir, f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            image.save_to_disk(filename)
            print(f"Fotoğraf kaydedildi: {filename}")

        camera.listen(lambda image: save_image(image))

        return camera
    except Exception as e:
        print(f"Kamera bağlanırken veya fotoğraf çekerken hata oluştu: {e}")
        return None

# Kamera Perspektifi Kontrolü
def adjust_camera_perspective(camera, pitch=0.0, yaw=0.0, roll=0.0):
    try:
        if camera:
            transform = camera.get_transform()
            transform.rotation.pitch = pitch
            transform.rotation.yaw = yaw
            transform.rotation.roll = roll
            camera.set_transform(transform)
            print(f"Kamera perspektifi ayarlandı: Pitch={pitch}, Yaw={yaw}, Roll={roll}")
        else:
            print("Kamera mevcut değil, perspektif ayarlanamıyor.")
    except Exception as e:
        print(f"Kamera perspektifi ayarlanırken hata oluştu: {e}")

# Lidar Ekleyip Mesafe Ölçme
def attach_lidar_and_measure(vehicle, world):
    try:
        blueprint_library = world.get_blueprint_library()
        lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')

        # Lidar ayarları
        lidar_bp.set_attribute('channels', str(32))
        lidar_bp.set_attribute('points_per_second', str(100000))
        lidar_bp.set_attribute('rotation_frequency', str(10.0))
        lidar_bp.set_attribute('upper_fov', str(30.0))
        lidar_bp.set_attribute('lower_fov', str(-25.0))
        lidar_bp.set_attribute('horizontal_fov', str(360))
        lidar_bp.set_attribute('range', str(100.0))

        # Lidar araca bağlanır
        lidar_transform = carla.Transform(carla.Location(x=0.0, z=2.5))  # Araç üzerinde konumlandırma
        lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)
        print("Lidar başarıyla araca bağlandı.")

        def process_lidar_data(data):
            print(f"Lidar ölçümleri alındı: {len(data)} nokta")

        lidar.listen(lambda data: process_lidar_data(data))

        return lidar
    except Exception as e:
        print(f"Lidar bağlanırken veya ölçüm yapılırken hata oluştu: {e}")
        return None

# Çarpışma Sensörü Ekleme
def attach_collision_sensor(vehicle, world):
    try:
        blueprint_library = world.get_blueprint_library()
        collision_bp = blueprint_library.find('sensor.other.collision')

        # Çarpışma sensörü araca bağlanır
        collision_transform = carla.Transform(carla.Location(x=0.0, z=2.0))
        collision_sensor = world.spawn_actor(collision_bp, collision_transform, attach_to=vehicle)
        print("Çarpışma sensörü başarıyla araca bağlandı.")

        def handle_collision(event):
            print(f"Çarpışma algılandı! Nesne: {event.other_actor.type_id}")

        collision_sensor.listen(lambda event: handle_collision(event))

        return collision_sensor
    except Exception as e:
        print(f"Çarpışma sensörü bağlanırken hata oluştu: {e}")
        return None

# Main
if __name__ == "__main__":
    client = connect_to_carla()
    if client:
        world = client.get_world()

        # Araç ekle
        vehicle = spawn_vehicle(world)

        # Araç kontrol et
        control_vehicle(vehicle)

        # Şerit değiştirme
        if vehicle:
            change_lane(vehicle, direction="left")

        # Kamera ekle ve fotoğraf çek
        if vehicle:
            camera = attach_camera_and_capture(vehicle, world)

            # Kamera perspektifini ayarla
            if camera:
                adjust_camera_perspective(camera, pitch=-10.0, yaw=45.0, roll=0.0)

            # Lidar ekle ve mesafe ölç
            lidar = attach_lidar_and_measure(vehicle, world)

            # Çarpışma sensörü ekle
            collision_sensor = attach_collision_sensor(vehicle, world)

            # Şerit ihlali sensörü ekle
            lane_invasion_sensor = attach_lane_invasion_sensor(vehicle, world)
    else:
        print("CARLA'ya bağlanılamadı.")