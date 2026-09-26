from afds.order_frontier import OrderFrontier

def test_order_frontier_exact():
    d=OrderFrontier([0,4,10,11])
    z=d.frontier()
    assert z[0].left==10 and z[0].right==11 and z[0].radius==0.5
    assert [x.radius for x in z]==[0.5,2.0,3.0]

def test_answer_silent_order_frontier_update():
    d=OrderFrontier([0,4,10,11])
    before=d.nearest()
    # Insertion preserves the relative order of all old keys but changes frontier state.
    d.insert(10.5)
    after=d.nearest()
    assert before.radius==0.5 and after.radius==0.25
    assert d.values==(0.0,4.0,10.0,10.5,11.0)

def test_delete_repairs_local_frontier():
    d=OrderFrontier([0,4,10,10.5,11])
    d.delete(10.5)
    assert d.nearest().radius==0.5
