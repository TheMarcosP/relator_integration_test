# coding=utf-8
# Copyright 2019 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Script allowing to play the game by multiple players."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags
from absl import logging
import time
import json
import logging
from gfootball.env import config
from gfootball.env import football_env
from module_a.parse_observation import parse_observation # our function to parse the observation
from module_a.send_event import EventSender # object to send events

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'players', 'bot:left_players=1;bot:right_players=1',
    'Both teams controlled by built-in AI'
)
flags.DEFINE_string('level', '', 'Level to play')
flags.DEFINE_enum('action_set', 'full', ['default', 'full'], 'Action set')
flags.DEFINE_bool('real_time', True, 'AI vs AI does not need real time')
flags.DEFINE_bool('render', True, 'Disable rendering for speed')

logger = logging.getLogger(__name__)

def main(_):
  players = FLAGS.players.split(';') if FLAGS.players else ''
  assert not (any(['agent' in player for player in players])
             ), ('Player type \'agent\' can not be used with play_game.')
  cfg_values = {
      'action_set': FLAGS.action_set,
      'dump_full_episodes': True,
      'players': players,
      'real_time': FLAGS.real_time,
  }
  if FLAGS.level:
    cfg_values['level'] = FLAGS.level
  cfg = config.Config(cfg_values)
  env = football_env.FootballEnv(cfg)
  if FLAGS.render:
    env.render()
  env.reset()

  obs = env.reset()
  step = 0

  sender = EventSender() # (1) CREATE SENDER

  try:
    while True:
      next_obs, reward, done, info = env.step([]) # (2) do a step in the game

      try:
          summary = parse_observation(next_obs) # (3) PARSE OBSERVATION
          logger.info(f"✅ Observation Summary for (id={step}):\n{json.dumps(summary, indent=4)}")
      except Exception as e:
          logger.error(f"❌ Could not parse observation: {e}")
      
      try:
        # check the type of each key and value in summary if its not a str cast it to str (for grpc)
        for key, value in summary.items():
          if not isinstance(value, str):
            summary[key] = str(value)
        sender.send_async(str(step), summary) # (4) SEND EVENT (id, data)
        logger.info(f"✅ Sent event (id={step})")
      except Exception as e:
        logging.error(f"❌ Failed to send event: {e}")

      # Delay to make it readable
      time.sleep(10)

      # Prepare next iter
      obs = next_obs
      step += 1

      if done:
        print("Episode finished — resetting env.\n")
        obs = env.reset()
        step = 0

  except KeyboardInterrupt:
    logging.warning('Game stopped, writing dump...')
    env.write_dump('shutdown')
    exit(1)


if __name__ == '__main__':
  app.run(main)
