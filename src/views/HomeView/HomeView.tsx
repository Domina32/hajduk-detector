import { Button, Dialog, Flex } from '@radix-ui/themes';
import { add, format, isBefore, isToday, startOfToday } from 'date-fns';
import schedule from '../../mocks/mock.json';
import styles from './HomeView.module.css';
import Schedule from './partials/Schedule/Schedule';

const HomeView = () => {
  const todayGames = schedule.filter((entry) => isToday(new Date(entry.datetime)));
  const soonGames = schedule.filter((entry) =>
    isBefore(
      new Date(entry.datetime),
      add(startOfToday(), {
        years: 0,
        months: 1,
        weeks: 0,
        days: 0,
        hours: 0,
        minutes: 0,
        seconds: 0,
      }),
    ),
  );

  return (
    <Flex height="100%" align="center" direction="column">
      <Dialog.Root>
        <Dialog.Trigger>
          <Button>View full schedule</Button>
        </Dialog.Trigger>

        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>All games</Dialog.Title>
          <Dialog.Description size="2" mb="4">
            <Schedule games={schedule} />
          </Dialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Close
              </Button>
            </Dialog.Close>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>

      <Flex direction="column" className={styles.current}>
        Today&lsquo;s game:&nbsp;
        {todayGames.length === 0
          ? 'no games today'
          : todayGames.map((entry) => (
              <Flex key={entry.datetime}>
                on at {entry.location} at {format(new Date(entry.datetime), 'HH:mm')}
              </Flex>
            ))}
      </Flex>

      <Flex direction="column">
        Games in the next month:&nbsp;
        <Schedule games={soonGames} />
      </Flex>
    </Flex>
  );
};

export default HomeView;
