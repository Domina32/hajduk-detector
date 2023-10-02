import { Flex } from '@radix-ui/themes';
import { format, isToday } from 'date-fns';
import schedule from '../../mocks/mock.json';
import styles from './HomeView.module.css';

const HomeView = () => {
  const entries = schedule.filter((entry) => isToday(new Date(entry.datetime)));

  return (
    <Flex height="100%" align="center" direction="column">
      <Flex direction="column" className={styles.current}>
        Today&lsquo;s game:
        {entries.length === 0
          ? 'no games today'
          : entries.map((entry) => (
              <Flex key={entry.datetime}>
                on at {entry.location} at {format(new Date(entry.datetime), 'HH:mm')}
              </Flex>
            ))}
      </Flex>

      <Flex asChild direction="column" gap="5" grow="1">
        <ol>
          {schedule.map(({ location, datetime }) => (
            <Flex asChild key={datetime}>
              <li>
                {format(new Date(datetime), 'MM/dd/yyyy HH:mm')} at {location}
              </li>
            </Flex>
          ))}
        </ol>
      </Flex>
    </Flex>
  );
};

export default HomeView;
