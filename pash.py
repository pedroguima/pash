#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import boto3

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token


# Tree structure to keep track of where we are in the directory
class Node(object):
    def __init__(self, data, parent=None):
        if parent:
            parent.children.append(self)
            self.parent = parent
        else:
            self.parent = parent

        self.data = data
        self.children = []

    def set_parent(self, node):
        node.children.append(self)
        self.parent = node

    def append_child(self, node):
        node.parent = self
        self.children.append(node)

    def path(self):
        parents = []
        parent = self.parent
        while parent:
            parents.append(parent)
            parent = parent.parent
        return '/'.join([node.data for node in reversed(parents)]) + '/' + self.data

    def __str__(self):
        return 'Node({})'.format(self.path())

    def __repr__(self):
        return '<Node: {}, children {}>'.format(self.path(), self.children)


# Create tree structure
# TODO: This should be build using some sort of spec file
root = Node('/')
region = Node('eu-west-1', parent=root)
ec2 = Node('ec2', parent=region)
vpc = Node('vpc', parent=region)
s3 = Node('s3', parent=region)


def s3_ls(s3):
    for bucket in s3.buckets.all():
        print(bucket.name)


def ec2_ls(ec2):
    for instance in ec2.instances.all():
        print(instance.id)


def vpc_ls(ec2):
    for vpc in ec2.vpcs.all():
        print(vpc.id)


# TODO: Handle dispatch in a better way than this
ls = { 's3': s3_ls, 'ec2': ec2_ls, 'vpc': vpc_ls }


def toolbar(cli):
    return [(Token.Toolbar, region.data)]

style = style_from_dict({
        Token.Toolbar: '#ffffff bg:#333333',
})


def main():
    history = InMemoryHistory()

    service = root

    while True:
        #TODO: Clean up the UI
        completer = WordCompleter([s.data for s in service.children], ignore_case=True)
        text = prompt('{}> '.format(service.path()), history=history, completer=completer, get_bottom_toolbar_tokens=toolbar, style=style).split()
        command, args = text[0], ''.join(text[1:])

        # Commands for the shell
        if command == 'cd':
            if not args:
                service = root
            elif args.startswith('..'):
                service = service.parent
            else:
                for child in service.children:
                    if child.data == args:
                        service = child
                        break
                else:
                    print('service not found...')

        if command == 'ls':
            if service.children:
                for child in service.children:
                    print(child.data)
            else:
                client = service.data

                # VPC is actually accessed thru ec2
                # TODO: Make a mapping of some sort
                if client == 'vpc':
                    client = 'ec2'

                s = boto3.resource(client)
                ls[service.data](s)


if __name__ == '__main__':
    try:
        main()
    except EOFError:
        pass

