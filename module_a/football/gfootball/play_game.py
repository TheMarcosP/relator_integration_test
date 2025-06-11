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

from gfootball.env import config
from gfootball.env import football_env

FLAGS = flags.FLAGS

flags.DEFINE_string('players', 'keyboard:left_players=1',
                    'Semicolon separated list of players, single keyboard '
                    'player on the left by default')
flags.DEFINE_string('level', '', 'Level to play')
flags.DEFINE_enum('action_set', 'default', ['default', 'full'], 'Action set')
flags.DEFINE_bool('real_time', True,
                  'If true, environment will slow down so humans can play.')
flags.DEFINE_bool('render', True, 'Whether to do game rendering.')


def parse_observation(obs):
    summary = {}
    summary["ball_position"], summary["ball_movement"] = parse_ball_info(obs)
    summary["ball_owner"] = parse_ball_owner(obs)
    summary["controlled_player"] = parse_controlled_player(obs)
    summary["current_actions"] = parse_sticky_actions(obs)
    summary["game_mode"] = parse_game_mode(obs)
    summary["score"] = parse_score(obs)
    summary["steps_left"] = parse_steps_left(obs)
    return summary


def parse_ball_info(obs):
    x, y = obs.get('ball', [None, None])[0:2]
    ball_position = describe_ball_position(x, y) if x is not None and y is not None else "Unknown"
    ball_direction = obs.get('ball_direction', None)
    if ball_direction is not None and len(ball_direction) > 0:
        ball_movement = f"Moving {'left' if ball_direction[0] < 0 else 'right'}"
    else:
        ball_movement = "Unknown"
    return ball_position, ball_movement


def parse_ball_owner(obs):
    ball_owned_team = obs.get("ball_owned_team", -1)
    ball_owned_player = obs.get("ball_owned_player", -1)
    if ball_owned_team == -1:
        return "No one owns the ball"
    else:
        team = "Left" if ball_owned_team == 0 else "Right"
        player_id = ball_owned_player
        roles_key = f"{team.lower()}_team_roles"
        if roles_key in obs and player_id >= 0 and player_id < len(obs[roles_key]):
            role = role_to_string(obs[roles_key][player_id])
        else:
            role = f"Player {player_id}"
        return f"{team} team's {role} (Player {player_id})"


def parse_controlled_player(obs):
    controlled_id = obs.get("left_agent_controlled_player", [None])[0]
    if controlled_id is not None and 'left_team_roles' in obs and controlled_id < len(obs['left_team_roles']):
        return f"Controlling player {controlled_id} of Left team as {role_to_string(obs['left_team_roles'][controlled_id])}"
    else:
        return "Unknown controlled player"


def parse_sticky_actions(obs):
    sticky = []
    if 'left_agent_sticky_actions' in obs and len(obs['left_agent_sticky_actions']) > 0:
        sticky_actions = obs['left_agent_sticky_actions'][0]
        if hasattr(sticky_actions, 'tolist'):
            sticky_actions = sticky_actions.tolist()
        sticky = [i for i, val in enumerate(sticky_actions) if val == 1]
    return ", ".join([sticky_action_name(i) for i in sticky]) if sticky else "None"


def parse_game_mode(obs):
    if 'game_mode' in obs:
        return game_mode_name(obs["game_mode"])
    else:
        return "Unknown"


def parse_score(obs):
    if 'score' in obs and len(obs['score']) == 2:
        return f"{obs['score'][0]} - {obs['score'][1]}"
    else:
        return "Unknown"


def parse_steps_left(obs):
    return obs.get('steps_left', 'Unknown')


def describe_ball_position(x, y):
    # X-axis zones
    if x < -0.66:
        horizontal = "left defensive third"
    elif x < -0.33:
        horizontal = "left midfield"
    elif x < 0.33:
        horizontal = "center midfield"
    elif x < 0.66:
        horizontal = "right midfield"
    else:
        horizontal = "right attacking third"

    # Y-axis zones
    if y < -0.28:
        vertical = "top"
    elif y > 0.28:
        vertical = "bottom"
    else:
        vertical = "central"

    return f"{horizontal}, {vertical} area"


def role_to_string(role_id):
    roles = [
        "Goalkeeper", 
        "Centre Back", 
        "Left Back", 
        "Right Back", 
        "Defensive Midfielder", 
        "Central Midfielder", 
        "Left Midfielder", 
        "Right Midfielder", 
        "Attacking Midfielder", 
        "Centre Forward"
    ]
    return roles[role_id] if 0 <= role_id < len(roles) else f"Unknown Role {role_id}"


def sticky_action_name(index):
    actions = [
        "move left", "move top-left", "move top", "move top-right",
        "move right", "move bottom-right", "move bottom", "move bottom-left",
        "sprint", "dribble"
    ]
    return actions[index] if 0 <= index < len(actions) else f"Unknown Action {index}"


def game_mode_name(mode_id):
    modes = [
        "Normal", "Kick Off", "Goal Kick", "Free Kick",
        "Corner", "Throw In", "Penalty"
    ]
    return modes[mode_id] if 0 <= mode_id < len(modes) else f"Unknown Mode {mode_id}"


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
  
  try:
    while True:

      action = []

      # Step environment
      next_obs, reward, done, info = env.step(action)

      # Log to console
      # print(f"Step {step}")
      # print(f"  Action : {action}")
      # print(f"  Reward : {reward}")
      # print(f"  Done   : {done}")
      # print(f"  Info   : {info}")
      # print(f"  Obs    : {next_obs!r}")
      # print('-' * 80)

      # Print parsed observation summary
      try:
          summary = parse_observation(next_obs)
          print("Observation Summary:")
          for k, v in summary.items():
              print(f"  {k}: {v}")
          print('-' * 80)
      except Exception as e:
          print(f"Could not parse observation: {e}")
          print('-' * 80)

      # Delay to make it readable
      # time.sleep(1.0)

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
