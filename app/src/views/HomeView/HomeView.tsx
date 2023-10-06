import { Button, Container, Dialog, Flex, Text } from '@radix-ui/themes';
import { add, format, isAfter, isBefore, isToday, startOfToday } from 'date-fns';
import schedule from '../../mocks/scraped.json';
import styles from './HomeView.module.css';
import Schedule from './partials/Schedule/Schedule';

const HomeView = () => {
  const todayGames = schedule.filter((entry) => isToday(new Date(entry.datetime)));
  const soonGames = schedule.filter(
    (entry) =>
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
      ) && isAfter(new Date(entry.datetime), startOfToday()),
  );

  return (
    <Container size="1">
      <Flex height="100%" align="start" direction="column">
        <Dialog.Root>
          <Dialog.Trigger>
            <Button m="3">
              <Text>View full schedule</Text>
            </Button>
          </Dialog.Trigger>

          <Dialog.Content style={{ maxWidth: 450 }}>
            <Dialog.Title>
              <Text>All games</Text>
            </Dialog.Title>

            <Schedule games={schedule} />

            <Flex gap="3" mt="4" justify="end">
              <Dialog.Close>
                <Button variant="soft" color="gray">
                  <Text>Close</Text>
                </Button>
              </Dialog.Close>
            </Flex>
          </Dialog.Content>
        </Dialog.Root>

        <Flex direction="column" align="start" justify="center" p="4" className={styles.current}>
          <Text>Today&lsquo;s game:&nbsp;</Text>
          {todayGames.length === 0 ? (
            <Text>no games today</Text>
          ) : (
            todayGames.map((entry) => (
              <Flex key={entry.datetime}>
                <Text>
                  on at {entry.location} at {format(new Date(entry.datetime), 'HH:mm')}
                </Text>
              </Flex>
            ))
          )}
        </Flex>

        <Flex direction="column" width="100%" p="5">
          <Text>Games in the next month:&nbsp;</Text>
          <Schedule games={soonGames} />
        </Flex>
      </Flex>
    </Container>
  );
};

export default HomeView;
