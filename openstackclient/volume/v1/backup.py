#   Copyright 2012-2013 OpenStack Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""Volume v1 Backup action implementations"""

import copy
import six

from openstackclient.common import command
from openstackclient.common import utils


class CreateBackup(command.ShowOne):
    """Create new backup"""

    def get_parser(self, prog_name):
        parser = super(CreateBackup, self).get_parser(prog_name)
        parser.add_argument(
            'volume',
            metavar='<volume>',
            help='Volume to backup (name or ID)',
        )
        parser.add_argument(
            '--container',
            metavar='<container>',
            required=False,
            help='Optional backup container name',
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='Name of the backup',
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            help='Description of the backup',
        )
        return parser

    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        volume_id = utils.find_resource(volume_client.volumes,
                                        parsed_args.volume).id
        backup = volume_client.backups.create(
            volume_id,
            parsed_args.container,
            parsed_args.name,
            parsed_args.description
        )

        backup._info.pop('links')
        return zip(*sorted(six.iteritems(backup._info)))


class DeleteBackup(command.Command):
    """Delete backup(s)"""

    def get_parser(self, prog_name):
        parser = super(DeleteBackup, self).get_parser(prog_name)
        parser.add_argument(
            'backups',
            metavar='<backup>',
            nargs="+",
            help='Backup(s) to delete (ID only)',
        )
        return parser

    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        for backup in parsed_args.backups:
            backup_id = utils.find_resource(volume_client.backups,
                                            backup).id
            volume_client.backups.delete(backup_id)


class ListBackup(command.Lister):
    """List backups"""

    def get_parser(self, prog_name):
        parser = super(ListBackup, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            default=False,
            help='List additional fields in output',
        )
        return parser

    def take_action(self, parsed_args):

        def _format_volume_id(volume_id):
            """Return a volume name if available

            :param volume_id: a volume ID
            :rtype: either the volume ID or name
            """

            volume = volume_id
            if volume_id in volume_cache.keys():
                volume = volume_cache[volume_id].display_name
            return volume

        if parsed_args.long:
            columns = ['ID', 'Name', 'Description', 'Status', 'Size',
                       'Availability Zone', 'Volume ID', 'Container']
            column_headers = copy.deepcopy(columns)
            column_headers[6] = 'Volume'
        else:
            columns = ['ID', 'Name', 'Description', 'Status', 'Size']
            column_headers = columns

        # Cache the volume list
        volume_cache = {}
        try:
            for s in self.app.client_manager.volume.volumes.list():
                volume_cache[s.id] = s
        except Exception:
            # Just forget it if there's any trouble
            pass

        data = self.app.client_manager.volume.backups.list()

        return (column_headers,
                (utils.get_item_properties(
                    s, columns,
                    formatters={'Volume ID': _format_volume_id},
                ) for s in data))


class RestoreBackup(command.Command):
    """Restore backup"""

    def get_parser(self, prog_name):
        parser = super(RestoreBackup, self).get_parser(prog_name)
        parser.add_argument(
            'backup',
            metavar='<backup>',
            help='Backup to restore (ID only)')
        parser.add_argument(
            'volume',
            metavar='<volume>',
            help='Volume to restore to (name or ID)')
        return parser

    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        backup = utils.find_resource(volume_client.backups,
                                     parsed_args.backup)
        destination_volume = utils.find_resource(volume_client.volumes,
                                                 parsed_args.volume)
        return volume_client.restores.restore(backup.id,
                                              destination_volume.id)


class ShowBackup(command.ShowOne):
    """Display backup details"""

    def get_parser(self, prog_name):
        parser = super(ShowBackup, self).get_parser(prog_name)
        parser.add_argument(
            'backup',
            metavar='<backup>',
            help='Backup to display (ID only)')
        return parser

    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        backup = utils.find_resource(volume_client.backups,
                                     parsed_args.backup)
        backup._info.pop('links')
        return zip(*sorted(six.iteritems(backup._info)))
