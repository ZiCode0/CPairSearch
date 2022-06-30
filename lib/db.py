import sqlite3

target_db_path = '../../local.db'


class LocalDb:
    def __init__(self, db_path=None):
        if db_path:
            self.target_path = db_path
        else:
            self.target_path = target_db_path
        self.conn = sqlite3.connect(self.target_path)
        self.cursor = self.conn.cursor()

    def _get_cmd(self, query) -> list:
        """
        Base select query instance
        :param query: query string
        :return: list of objects
        """
        response = self.cursor.execute(query).fetchall()
        return response

    def _set_cmd(self, query) -> bool:
        self.cursor.execute(query)
        # save results
        self.conn.commit()
        # internal code response: ok/True
        return True

    def exclude_get(self, target_user_id=0):
        # set target user id to select exclude rules
        query_str = 'SELECT * FROM exclude WHERE user_id={user_id};'.format(user_id=target_user_id)
        # make query request
        response = self._get_cmd(query_str)
        return response

    def exclude_add(self, target_rule, target_user_id=0):
        # set target user id to select exclude rules
        query_str = f"INSERT INTO exclude (user_id, rule) VALUES ({target_user_id}, '{target_rule}');"
        # .format(target_rule=target_rule,
        # user_id=target_user_id)
        return self._set_cmd(query_str)

    def exclude_clear(self, target_rule=None, target_user_id=0):
        # set target user id to select exclude rules
        query_str = "DELETE FROM exclude WHERE user_id={target_user_id};".format(target_user_id=target_user_id)
        if target_rule:
            query_str += ' AND rule={target_rule}'.format(target_rule=target_rule)
        return self._set_cmd(query_str)


if __name__ == '__main__':
    ldb = LocalDb()
    res = ldb.exclude_get()
    # print()
