import { Box, Flex, Text } from '@radix-ui/themes';
import { format } from 'date-fns';
import styles from './Schedule.module.css';

interface Game {
  datetime: string;
  location: string;
}

interface ScheduleProps {
  games: Game[];
}

const Schedule: React.FC<ScheduleProps> = ({ games }) => (
  <Flex asChild direction="column" gap="5" grow="1">
    <ol>
      <Flex asChild className={styles.header} pl="4" pr="4">
        <li>
          <Box grow="1" style={{ width: '70%' }}>
            <Text weight="medium">Date & time</Text>
          </Box>
          <Box grow="1" style={{ width: '30%' }}>
            <Text weight="medium">Location</Text>
          </Box>
        </li>
      </Flex>
      {games.map(({ datetime, location }) => (
        <Flex asChild key={datetime}>
          <li>
            <Box grow="1" style={{ width: '70%' }}>
              <Text>{format(new Date(datetime), 'MM/dd/yyyy HH:mm')}</Text>
            </Box>
            <Box grow="1" style={{ width: '30%' }}>
              <Text>{location}</Text>
            </Box>
          </li>
        </Flex>
      ))}
    </ol>
  </Flex>
);

export default Schedule;
