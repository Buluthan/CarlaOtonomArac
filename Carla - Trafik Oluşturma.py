#!/usr/bin/env python

import glob
import os
import sys
import time
import argparse
import logging
from numpy import random
import carla

# Trafik yöneticisini kurar ve gerekli ayarları yapar
def setup_traffic_manager(client, args):
    traffic_manager = client.get_trafficmanager(args.tm_port)
    traffic_manager.set_global_distance_to_leading_vehicle(3.0)  # Öndeki araçla mesafe ayarı
    if args.respawn:
        traffic_manager.set_respawn_dormant_vehicles(True)  # Uyuyan araçları yeniden oluşturma
    if args.hybrid:
        traffic_manager.set_hybrid_physics_mode(True)  # Hibrit mod etkinleştirme
        traffic_manager.set_hybrid_physics_radius(100.0)  # Hibrit fizik modu yarıçapı
    if args.seed is not None:
        traffic_manager.set_random_device_seed(args.seed)  # Rastgelelik için tohum ayarı
    traffic_manager.global_percentage_speed_difference(30.0)  # Hız farkını ayarla
    return traffic_manager

# Belirli bir filtreye ve nesil seçimine göre blueprintleri getirir
def get_blueprints(world, filter_pattern, generation):
    blueprints = world.get_blueprint_library().filter(filter_pattern)
    if generation != "all":
        blueprints = [bp for bp in blueprints if int(bp.get_attribute('generation').as_int()) == int(generation)]
    return blueprints

# Araçları oluşturur ve dünyaya ekler
def spawn_vehicles(world, traffic_manager, args, spawn_points):
    vehicles_list = []
    blueprints = get_blueprints(world, args.filterv, args.generationv)
    random.shuffle(spawn_points)
    spawn_points = spawn_points[:args.number_of_vehicles]
    batch = []
    for transform in spawn_points:
        blueprint = random.choice(blueprints)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)  # Araç rengi belirleme
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)  # Sürücü kimliği ayarı
        blueprint.set_attribute('role_name', 'autopilot')  # Otopilot rolü atama
        batch.append(carla.command.SpawnActor(blueprint, transform).then(
            carla.command.SetAutopilot(carla.command.FutureActor, True, traffic_manager.get_port())))

    responses = world.get_client().apply_batch_sync(batch, True)
    for response in responses:
        if response.error:
            logging.error(response.error)
        else:
            vehicles_list.append(response.actor_id)
    
    # Tüm araçları otopilota ayarla
    for vehicle_id in vehicles_list:
        vehicle = world.get_actor(vehicle_id)
        if vehicle:
            vehicle.set_autopilot(True, traffic_manager.get_port())
    return vehicles_list

# Yayaları oluşturur ve dünyaya ekler
def spawn_walkers(world, args):
    walkers_list = []
    walker_blueprints = get_blueprints(world, args.filterw, args.generationw)
    walker_spawn_points = []
    for _ in range(args.number_of_walkers):
        loc = world.get_random_location_from_navigation()
        if loc:
            walker_spawn_points.append(carla.Transform(loc))  # Yaya spawn noktası seçimi

    walker_batch = []
    walker_speed = []
    for transform in walker_spawn_points:
        blueprint = random.choice(walker_blueprints)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false') 
        if blueprint.has_attribute('speed'):
            speed = random.choice(blueprint.get_attribute('speed').recommended_values)
            walker_speed.append(float(speed))
        else:
            walker_speed.append(1.4)  # Varsayılan yürüme hızı
        walker_batch.append(carla.command.SpawnActor(blueprint, transform))

    walker_responses = world.get_client().apply_batch_sync(walker_batch, True)
    walker_controllers = []
    for response in walker_responses:
        if response.error:
            logging.error(response.error)
        else:
            walkers_list.append(response.actor_id)
            walker_controllers.append({'id': response.actor_id})

    walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    walker_controller_batch = []
    for walker in walker_controllers:
        walker_controller_batch.append(carla.command.SpawnActor(walker_controller_bp, carla.Transform(), walker['id']))

    controller_responses = world.get_client().apply_batch_sync(walker_controller_batch, True)
    for i, response in enumerate(controller_responses):
        if response.error:
            logging.error(response.error)
        else:
            walker_controllers[i]['controller_id'] = response.actor_id

    all_actors = world.get_actors([walker['id'] for walker in walker_controllers] + [walker['controller_id'] for walker in walker_controllers])
    for actor in all_actors:
        actor.start()
        actor.go_to_location(world.get_random_location_from_navigation())
    return [walker['id'] for walker in walker_controllers] + [walker['controller_id'] for walker in walker_controllers]

def control_traffic_lights(world):
    # Dünya üzerinde tüm trafik ışıklarını al
    traffic_lights = world.get_actors().filter('traffic.traffic_light')
    
    for traffic_light in traffic_lights:
        # Trafik ışığını yeşil yap
        traffic_light.set_state(carla.TrafficLightState.Green)
        # Yeşil ışığın süresini ayarla
        traffic_light.set_green_time(10.0)
        # Sarı ve kırmızı sürelerini ayarla
        traffic_light.set_yellow_time(3.0)
        traffic_light.set_red_time(5.0)
        
        print(f"Trafik ışığı durumu: {traffic_light.state}")


def main():
    parser = argparse.ArgumentParser(description="CARLA Trafik Simülasyonu Scripti")
    parser.add_argument('--host', default='127.0.0.1', help='Sunucu IP adresi')
    parser.add_argument('--port', default=2000, type=int, help='Sunucu Portu')
    parser.add_argument('--tm-port', default=8000, type=int, help='Trafik Yöneticisi Portu')
    parser.add_argument('--number-of-vehicles', default=50, type=int, help='Oluşturulacak araç sayısı')
    parser.add_argument('--number-of-walkers', default=20, type=int, help='Oluşturulacak yaya sayısı')
    parser.add_argument('--filterv', default='vehicle.*', help='Araç filtresi')
    parser.add_argument('--filterw', default='walker.pedestrian.*', help='Yaya filtresi')
    parser.add_argument('--generationv', default='all', help='Araç nesli')
    parser.add_argument('--generationw', default='2', help='Yaya nesli')
    parser.add_argument('--respawn', action='store_true', help='Uyuyan araçları yeniden oluştur')
    parser.add_argument('--hybrid', action='store_true', help='Hibrit modu etkinleştir')
    parser.add_argument('--seed', type=int, help='Rastgelelik için tohum ayarı')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)

    control_traffic_lights(world)

    try:
        world = client.get_world()
        traffic_manager = setup_traffic_manager(client, args)

        spawn_points = world.get_map().get_spawn_points()
        if len(spawn_points) < args.number_of_vehicles:
            logging.warning("Talep edilen araç sayısı mevcut spawn noktalarını aşıyor")

        vehicles = spawn_vehicles(world, traffic_manager, args, spawn_points)
        walkers = spawn_walkers(world, args)

        logging.info(f"{len(vehicles)} araç ve {len(walkers)} yaya oluşturuldu")

        while True:
            world.wait_for_tick()

    except KeyboardInterrupt:
        logging.info("Trafik simülasyonu kullanıcı tarafından kesildi")
    finally:
        logging.info("Aktörler temizleniyor")
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles + walkers])
        logging.info("Simülasyon sona erdi")

if __name__ == '__main__':
    main()
