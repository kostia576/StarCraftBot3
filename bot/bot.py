import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.player import Bot, Computer
import cv2
import numpy as np
import random
from sc2 import position
class CompetitiveBot(BotAI):
    NAME: str = "CompetitiveBot"
    """This bot's name"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    def __init__(self):
        self.proxy_built = False


    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_gateway()
        await self.build_gas()
        await self.build_four_gates()
        await self.build_cyber_core()
        await self.train_stalkers()
        await self.chrono()
        await self.warpgate_research()
        await self.attack()
        await self.warp_stalkers()
        await self.micro()
        await self.intel()
        await self.robotics()
        await self.scout()
        pass


    def random_location_variance(self, enemy_start_location):
        x = enemy_start_location[0]
        y = enemy_start_location[1]
        x += ((random.randrange(-20, 20))/100) * enemy_start_location[0]
        y += ((random.randrange(-20, 20))/100) * enemy_start_location[1]
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x > self.game_info.map_size[0]:
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            y = self.game_info.map_size[1]
        go_to = position.Point2(position.Pointlike((x, y)))
        return go_to
    async def intel(self):

        print(self.game_info.map_size)
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
        draw_dict = {
                     UnitTypeId.NEXUS: [15, (0, 255, 0)],
                     UnitTypeId.PYLON: [3, (20, 235, 0)],
                     UnitTypeId.PROBE: [1, (55, 200, 0)],
                     UnitTypeId.ASSIMILATOR: [2, (55, 200, 0)],
                     UnitTypeId.GATEWAY: [3, (200, 100, 0)],
                     UnitTypeId.CYBERNETICSCORE: [3, (150, 150, 0)],
                     UnitTypeId.STARGATE: [5, (255, 0, 0)],
                     UnitTypeId.VOIDRAY: [3, (255, 100, 0)],
                     UnitTypeId.ROBOTICSFACILITY: [5, (215, 155, 0)]
                    }
        for unit_type in draw_dict:
            for unit in self.structures(unit_type).ready:
                pos = unit.position
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), draw_dict[unit_type][0], draw_dict[unit_type][1], -1)

        main_base_names = ["nexus", "supplydepot", "hatchery"]

        for enemy_building in self.enemy_structures:
            pos = enemy_building.position
            if enemy_building.name.lower() not in main_base_names:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), 5, (200, 50, 212), -1)
        for enemy_building in self.enemy_structures:
            pos = enemy_building.position
            if enemy_building.name.lower() in main_base_names:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), 15, (0, 0, 255), -1)

        for enemy_unit in self.enemy_units:
            if not enemy_unit.is_structure:
                worker_names = ["probe",
                                "scv",
                                "drone"]
                # if that unit is a PROBE, SCV, or DRONE... it's a worker
                pos = enemy_unit.position
                if enemy_unit.name.lower() in worker_names:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (55, 0, 155), -1)
                else:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])), 3, (50, 0, 215), -1)
        for obs in self.structures(UnitTypeId.OBSERVER).ready:
            pos = obs.position
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (255, 255, 255), -1)
        # flip horizontally to make our final fix in visual representation:
        flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)
        cv2.imshow('Intel', resized)
        cv2.waitKey(1)


    async def build_workers(self):
        nexus = self.townhalls.ready.random
        if (
          self.can_afford(UnitTypeId.PROBE)
          and nexus.is_idle
          and self.workers.amount < self.townhalls.amount * 22

        ):
            nexus.train(UnitTypeId.PROBE)

    async def build_pylons(self):
        nexus = self.townhalls.ready.random
        pos = nexus.position.towards(self.enemy_start_locations[0], 10)
        if (
          self.supply_left < 3
          and self.already_pending(UnitTypeId.PYLON)==0
          and self.can_afford(UnitTypeId.PYLON)
        ):
            await self.build(UnitTypeId.PYLON, near=pos)

        if (
            self.structures(UnitTypeId.GATEWAY).amount == 4
            and not self.proxy_built
            and self.can_afford(UnitTypeId.PYLON)
        ):
            pos = self.game_info.map_center.towards(self.enemy_start_locations[0])
            await self.build(UnitTypeId.PYLON, pos)
            self.proxy_built = True

    async def build_gateway(self):
        if (
            self.structures(UnitTypeId.PYLON).ready
            and self.can_afford(UnitTypeId.GATEWAY)
            and not self.structures(UnitTypeId.GATEWAY)
        ):
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            await self.build(UnitTypeId.GATEWAY, near=pylon)

    async def build_gas(self):
        if self.structures(UnitTypeId.GATEWAY):
            for nexus in self.townhalls.ready:
                vgs = self.vespene_geyser.closer_than(15, nexus)
                for vg in vgs:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break
                    if not self.gas_buildings or not self.gas_buildings.closer_than(1,vg):
                        worker.build(UnitTypeId.ASSIMILATOR, vg)
                        worker.stop(queue=True)

    async def build_cyber_core(self):
        if self.structures(UnitTypeId.PYLON).ready:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.structures(UnitTypeId.GATEWAY).ready:
                if not self.structures(UnitTypeId.CYBERNETICSCORE):
                    if(
                        self.can_afford(UnitTypeId.CYBERNETICSCORE)
                        and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
                    ):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)



    async def train_stalkers(self):
        for gateway in self.structures(UnitTypeId.GATEWAY).ready:
            if(
                self.can_afford(UnitTypeId.STALKER)
                and gateway.is_idle
            ):
                gateway.train(UnitTypeId.STALKER)

    async def build_four_gates(self):
        if(
            self.structures(UnitTypeId.PYLON).ready
            and self.can_afford(UnitTypeId.GATEWAY)
            and self.structures(UnitTypeId.GATEWAY).amount < 4
        ):
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            await self.build(UnitTypeId.GATEWAY, near=pylon)


    async def chrono(self):
        if self.structures(UnitTypeId.PYLON):
            nexus = self.townhalls.ready.random
            if (
                not self.structures(UnitTypeId.CYBERNETICSCORE).ready
                and self.structures(UnitTypeId.PYLON).amount > 0
            ):
                if nexus.energy >= 50:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
            else:
                cybercore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.random
                if nexus.energy >= 50:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, cybercore)



    async def warpgate_research(self):
        if (
            self.structures(UnitTypeId.CYBERNETICSCORE).ready
            and self.can_afford(AbilityId.RESEARCH_WARPGATE)
            and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
        ):
            cybercore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            cybercore.research(UpgradeId.WARPGATERESEARCH)

    async def attack(self):
        stalkercount = self.units(UnitTypeId.STALKER).amount
        stalkers = self.units(UnitTypeId.STALKER).ready.idle

        for stalker in stalkers:
            if stalkercount > 8:
                stalker.attack(self.enemy_start_locations[0])


    async def warp_stalkers(self):
        for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            proxy = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
            if AbilityId.WARPGATETRAIN_STALKER in abilities and self.can_afford(UnitTypeId.STALKER):
                placement = proxy.position.random_on_distance(3)
                warpgate.warp_in(UnitTypeId.STALKER, placement)

    async def micro(self):
        stalkers = self.units(UnitTypeId.STALKER)
        enemy_location = self.enemy_start_locations[0]

        if self.structures(UnitTypeId.PYLON).ready:
            pylon = self.structures(UnitTypeId.PYLON).closest_to(enemy_location)

            for stalker in stalkers:
                if stalker.weapon_cooldown == 0:
                    stalker.attack(enemy_location)
                elif stalker.weapon_cooldown < 0:
                    stalker.move(pylon)
                else:
                    stalker.move(pylon)

    async def robotics(self):
        if self.structures(UnitTypeId.PYLON).ready:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready.exists:
                if len(self.structures(UnitTypeId.ROBOTICSFACILITY)) < 1:
                    if self.can_afford(UnitTypeId.ROBOTICSFACILITY) and not self.already_pending(UnitTypeId.ROBOTICSFACILITY):
                        await self.build(UnitTypeId.ROBOTICSFACILITY, near=pylon)


    async def scout(self):
        if len(self.structures(UnitTypeId.OBSERVER)) > 0:
            scout = self.structures(UnitTypeId.OBSERVER)[0]
            if scout.is_idle:
                enemy_location = self.enemy_start_locations[0]
                move_to = self.random_location_variance(enemy_location)
                print(move_to)
                await self.do(scout.move(move_to))
        else:
            for rf in self.structures(UnitTypeId.ROBOTICSFACILITY).ready.prefer_idle:
                if self.can_afford(UnitTypeId.OBSERVER) and self.supply_left > 0:
                    await self.do(rf.train(UnitTypeId.OBSERVER))

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")