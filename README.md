# aiocvv
An API wrapper for Classeviva written in Python using asyncio.

It's made to be easy to use, and handles rate-limits and caching (using `shelve`) as the API has very strict rate-limits.

Teachers' endpoints haven't been implemented yet. If you are a teacher and/or you want to contribute, feel free to [open a pull request](https://github.com/Vinchethescript/aiocvv/pulls).

## Installation
```bash
pip install -U aiocvv
```

## Example usage
```python
import asyncio
from aiocvv import ClassevivaClient

async def main():
    client = ClassevivaClient("username", "password")
    await client.login() # IMPORTANT! Without this, client.me will be None
    print(client.me.name)

if __name__ == "__main__":
    asyncio.run(main())
```

You can also `await` the client class, so it will automatically login for you.
```python
import asyncio
from aiocvv import ClassevivaClient

async def main():
    client = await ClassevivaClient("username", "password")
    print(client.me.name)

if __name__ == "__main__":
    asyncio.run(main())
```

A more complex example showing most of what this library can do can be found [here](https://github.com/Vinchethescript/aiocvv/blob/main/example.py).

## Documentation
The documentation can be found [here](https://aiocvv.readthedocs.io/en/latest/).