import asyncio
import signal
import socket
import subprocess
import sys
import uvloop

from uvloop import _testbase as tb


class _TestProcess:
    def test_process_env_1(self):
        async def test():
            cmd = 'echo $FOO$BAR'
            env = {'FOO': 'sp', 'BAR': 'am'}
            proc = await asyncio.create_subprocess_shell(
                cmd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            exitcode = await proc.wait()
            self.assertEqual(exitcode, 0)

            out = await proc.stdout.read()
            self.assertEqual(out, b'spam\n')

        self.loop.run_until_complete(test())

    def test_process_cwd_1(self):
        async def test():
            cmd = 'pwd'
            env = {}
            cwd = '/'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            exitcode = await proc.wait()
            self.assertEqual(exitcode, 0)

            out = await proc.stdout.read()
            self.assertEqual(out, b'/\n')

        self.loop.run_until_complete(test())

    def test_process_executable_1(self):
        async def test():
            proc = await asyncio.create_subprocess_exec(
                b'doesnotexist', b'-c', b'print("spam")',
                executable=sys.executable,
                stdout=subprocess.PIPE,
                loop=self.loop)

            out, err = await proc.communicate()
            self.assertEqual(out, b'spam\n')

        self.loop.run_until_complete(test())

    def test_process_pid_1(self):
        async def test():
            prog = '''\
import os
print(os.getpid())
            '''

            cmd = sys.executable
            proc = await asyncio.create_subprocess_exec(
                cmd, b'-c', prog,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                loop=self.loop)

            pid = proc.pid
            expected_result = '{}\n'.format(pid).encode()

            out, err = await proc.communicate()
            self.assertEqual(out, expected_result)

        self.loop.run_until_complete(test())

    def test_process_send_signal_1(self):
        async def test():
            prog = '''\
import signal

def handler(signum, frame):
    if signum == signal.SIGUSR1:
        print('WORLD')

signal.signal(signal.SIGUSR1, handler)
a = input()
print(a)
a = input()
print(a)
exit(11)
            '''

            cmd = sys.executable
            proc = await asyncio.create_subprocess_exec(
                cmd, b'-c', prog,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            proc.stdin.write(b'HELLO\n')
            await proc.stdin.drain()

            self.assertEqual(await proc.stdout.readline(), b'HELLO\n')

            proc.send_signal(signal.SIGUSR1)

            proc.stdin.write(b'!\n')
            await proc.stdin.drain()

            self.assertEqual(await proc.stdout.readline(), b'WORLD\n')
            self.assertEqual(await proc.stdout.readline(), b'!\n')
            self.assertEqual(await proc.wait(), 11)

        self.loop.run_until_complete(test())

    def test_process_streams_1(self):
        async def test():

            prog = '''\
import sys
while True:
    a = input()
    if a == 'stop':
        exit(20)
    elif a == 'stderr':
        print('OUCH', file=sys.stderr)
    else:
        print('>' + a + '<')
            '''

            cmd = sys.executable
            proc = await asyncio.create_subprocess_exec(
                cmd, b'-c', prog,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            proc.stdin.write(b'foobar\n')
            out = await proc.stdout.readline()
            self.assertEqual(out, b'>foobar<\n')

            proc.stdin.write(b'stderr\n')
            out = await proc.stderr.readline()
            self.assertEqual(out, b'OUCH\n')

            proc.stdin.write(b'stop\n')

            exitcode = await proc.wait()
            self.assertEqual(exitcode, 20)

        self.loop.run_until_complete(test())


class Test_UV_Process(_TestProcess, tb.UVTestCase):
    pass


class Test_AIO_Process(_TestProcess, tb.AIOTestCase):
    pass