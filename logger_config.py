from loguru import logger
import sys


logger.remove(0)


logger.add(
    sink=sys.stdout,
    level='DEBUG',
    format='<level><b>{level}</b></level> | '
           '<g>{time:%d.%m.%Y %H:%M:%S}</g> | '
           '<m>{file}</m>:<m>{function}</m>:<m>{line}</m> | '
           '<level><b>{message}</b></level>'
)

logger.add(
    sink='info.log', 
    level='INFO', 
    format='[{time:%d.%m.%Y %H:%M:%S}] {file}:{function}:{line} {message}'
    )

logger.level('ERROR', color='<r>')
logger.level('DEBUG', color='<c>')
logger.level('INFO', color='<g>')
