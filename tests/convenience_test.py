import eventlet
from eventlet import event
from tests import LimitedTestCase

class TestServe(LimitedTestCase):
    def setUp(self):
        super(TestServe, self).setUp()
        from eventlet import debug
        debug.hub_exceptions(False)
        
    def tearDown(self):
        super(TestServe, self).tearDown()
        from eventlet import debug
        debug.hub_exceptions(True)
        
    def test_exiting_server(self):
        # tests that the server closes the client sock on handle() exit
        def closer(sock,addr):
            pass
            
        l = eventlet.listen(('localhost', 0))
        gt = eventlet.spawn(eventlet.serve, l, closer)
        client = eventlet.connect(('localhost', l.getsockname()[1]))
        client.sendall('a')
        self.assertEqual('', client.recv(100))
        gt.kill()


    def test_excepting_server(self):
        # tests that the server closes the client sock on handle() exception
        def crasher(sock,addr):
            x = sock.recv(1024)
            0/0
            
        l = eventlet.listen(('localhost', 0))
        gt = eventlet.spawn(eventlet.serve, l, crasher)
        client = eventlet.connect(('localhost', l.getsockname()[1]))
        client.sendall('a')
        self.assertRaises(ZeroDivisionError, gt.wait)
        self.assertEqual('', client.recv(100))

    def test_excepting_server_already_closed(self):
        # same as above but with explicit clsoe before crash
        def crasher(sock,addr):
            x = sock.recv(1024)
            sock.close()
            0/0
            
        l = eventlet.listen(('localhost', 0))
        gt = eventlet.spawn(eventlet.serve, l, crasher)
        client = eventlet.connect(('localhost', l.getsockname()[1]))
        client.sendall('a')
        self.assertRaises(ZeroDivisionError, gt.wait)
        self.assertEqual('', client.recv(100))

    def test_called_for_each_connection(self):
        hits = [0]
        def counter(sock, addr):
            hits[0]+=1
        l = eventlet.listen(('localhost', 0))
        gt = eventlet.spawn(eventlet.serve, l, counter)
        for i in xrange(100):
            client = eventlet.connect(('localhost', l.getsockname()[1]))
            self.assertEqual('', client.recv(100))            
        gt.kill()
        self.assertEqual(100, hits[0])
        
    def test_blocking(self):
        l = eventlet.listen(('localhost', 0))
        x = eventlet.with_timeout(0.01, 
            eventlet.serve, l, lambda c,a: None, 
            timeout_value="timeout")
        self.assertEqual(x, "timeout")

    def test_raising_stopserve(self):
        def stopit(conn, addr):
            raise eventlet.StopServe()
        l = eventlet.listen(('localhost', 0))
        # connect to trigger a call to stopit
        gt = eventlet.spawn(eventlet.connect, 
            ('localhost', l.getsockname()[1]))
        eventlet.serve(l, stopit)
        gt.wait()

    def test_concurrency(self):
        evt = event.Event()
        def waiter(sock, addr):
            sock.sendall('hi')
            evt.wait()
        l = eventlet.listen(('localhost', 0))
        gt = eventlet.spawn(eventlet.serve, l, waiter, 5)
        def test_client():
            c = eventlet.connect(('localhost', l.getsockname()[1]))
            # verify the client is connected by getting data
            self.assertEquals('hi', c.recv(2))
            return c
        clients = [test_client() for i in xrange(5)]
        # very next client should not get anything
        x = eventlet.with_timeout(0.01,
            test_client,
            timeout_value="timed out")
        self.assertEquals(x, "timed out")

        
        