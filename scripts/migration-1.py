import sqlite3

def migrate():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()

    cursor.execute('SELECT post_link_id FROM jobs')
    post_link_ids = cursor.fetchall()

    for (post_link_id,) in post_link_ids:
        try:
            comment_id = int(post_link_id)
            cursor.execute('INSERT OR IGNORE INTO seen_posts (comment_id) VALUES (?)', (comment_id,))
        except ValueError:
            print(f"Skipping invalid post_link_id: {post_link_id}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
