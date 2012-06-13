#!/bin/sh
#
# data/bug_script/debian_reportbug.sh
#
#  Copyright (c) 2009 Stephan Peijnik
#
#  Author: Stephan Peijnik <debian@sp.or.at>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#  USA.

if [ -z "$2" ]
then
    echo "Usage: $0 <info file> <file name or package name> <subject file>"
    exit 1
fi

invoke_as_user()
{
    user=$1
    command=$2
    if [ -z "$DISPLAY" ]
    then
	echo "Invoking $command via su as $user"
	su -pc "$command" "$user"
    else
	echo "Invoking $command via gksu as $user"
	gksu -k -u "$user" "$command"
    fi
}

if [ "$(id -ru)" = "0" ]
then
    chmod a+r $1
    chmod a+r $3
    echo "Running as root"
    if [ "$USER" != "root" ]
    then
	echo "Detected original user in USER env variable"
	invoke_as_user $USER "$0 $*"
    elif [ ! -z "$SUDO_USER" ]
    then
	echo "Detected original user in SUDO_USER env variable"
	invoke_as_user $SUDO_USER "$0 $*"
    else
	echo "Could not detect original user."
	exit 5
    fi
    exit 0
fi

ui="gtk2"

if [ -z "$DISPLAY" ]
then
    ui="urwid"
fi
subject="$(cat $3)"
reportbug --ui "$ui" -i "$1" -s "$subject" "$2"
