__author__ = 'david'

from sqlalchemy.sql import and_

from acme_orders.models import get_session, Order


def get_order_list(limit=None, offset=None, filters=None):
    desired_fields = ['id', 'valid', 'name']

    session = get_session()
    query = session.query(Order)

    applied_filters = []
    
    for k, v in filters.iteritems():
        if k == 'state':
            query_stmt = eval('Order.{}'.format(k))
            applied_filters.append(query_stmt.like('%{}%'.format(v)))
        else:
            applied_filters.append(eval('Order.{} == {}'.format(k, v)))

    query = query.filter(and_(*applied_filters))    
    query = query.limit(limit) if limit else query
    query = query.offset(offset) if offset else query
    orders = query.all()

    return ([
        {field: getattr(order, field) for field in desired_fields} 
            for order in orders
    ])



def get_order_by_id(order_id):
    desired_fields = [
        'id', 'valid', 'name', 'email', 'state', 
        'zipcode', 'errors', 'birthday'
    ]

    session = get_session()
    order = session.query(Order).filter(Order.id==order_id).first()

    imported_orders = {field: getattr(order, field) for field in desired_fields} 
    imported_orders['birthday'] = imported_orders['birthday'].strftime("%B %d, %Y")

    return imported_orders